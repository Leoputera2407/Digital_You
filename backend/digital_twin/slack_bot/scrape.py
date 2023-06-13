import ast

from datetime import datetime, timedelta, timezone
from postgrest.exceptions import APIError
from typing import Optional, List, Tuple
from slack_sdk import WebClient

from digital_twin.config.app_config import MIN_SCRAPED_THRESHOLD
from digital_twin.utils.logging import setup_logger
from digital_twin.db.slack_bot import update_chat_pairs, get_chat_pairs

logger = setup_logger()

def validate_target_users(target_users: Optional[List[str]], slack_user_id: str) -> None:
    if target_users is not None:
        if slack_user_id in target_users and len(target_users) == 1:
            raise ValueError("target_users cannot only contain the slack_user_id")

def is_interacted_with_target(user: str, target_users: Optional[List[str]], slack_user_id: str) -> bool:
    return target_users is None or user in target_users or user == slack_user_id

def join_user_channels(slack_user_id: str, client: WebClient):
    # Get the list of channels where the user is a member
    response = client.conversations_list(types="public_channel,private_channel", exclude_archived=True)

    for channel in response["channels"]:
        if slack_user_id in channel["members"]:
            # Join the channel
            client.conversations_join(channel=channel["id"])

def scrape_and_store_chat_history(
        command,
        slack_user_id: str, 
        team_id: str, 
        client: WebClient, 
        target_users: Optional[List[str]]= None, 
        min_message_length: int = 80, 
        cutoff_days: int = 365
    ) -> Optional[Tuple[List[str], List[Tuple[str, str]]]]:
    """
    Scrape the user's past interactions in Slack threads and store them in the Supabase database. 
    We'll only see `contiguous` interactions between slack_user_id and target_users.
    If target_users is None, then slack_user_id and all other users are considered.
    Caveat -- We only scrape messages inside threads, and not messages in channels.

    Args:
        slack_user_id (str): The Slack user ID for whom to scrape the chat history.
        team_id (str): The ID of the Slack team/channel from which to scrape the chat history.
        client (WebClient): The WebClient instance for making API calls to the Slack API.
        target_users (List[str]): List of Slack user IDs considered as target users.
        min_message_length (int, optional): Minimum length of a message to store. Defaults to 80.
        cutoff_days (int, optional): Number of days to consider for the chat history cutoff. Defaults to 365.

    Returns:
        Tuple[List[str], List[Tuple[str, str]]]: A tuple of two lists: `contiguous_chat_transcript` and `chat_pairs`.
        - `contiguous_chat_transcript`: A list of strings representing contiguous chat interactions between `slack_user_id` and `target_users`. 
        If `target_users` is `None`, the interactions are between `slack_user_id` and any other user.
        - `chat_pairs`: A list of tuples where each tuple represents a pair of chat messages. The first message in the pair is from a target user (or any user if `target_users` is `None`), and the second message is a response from `slack_user_id`.

    Example:
        Given `slack_user_id = "123"`, `team_id = "team1"`, `target_users = ["456", "789"]`, and the following interactions:

        - Message from "123": "Hello, how can I assist you today?"
        - Message from "456": "I have a question about the new feature."
        - Message from "123": "Sure, what do you need help with?"
        - Message from "999": "I'm just butting in here with a random message."
        - Message from "789": "Can you provide more details about the feature?"
        - Message from "123": "Of course, let me explain..."
        - Message from "456": "Thank you, that was helpful."
        - Message from "999": "Another random message from me."
        - Message from "123": "I'm glad I could assist."
        - Message from "789": "I have another question."
        - Message from "123": "Sure, ask away."

        The function would return:
        (
            [
                "123: Hello, how can I assist you today?\n456: I have a question about the new feature.\n123: Sure, what do you need help with?\n",
                "789: Can you provide more details about the feature?\n123: Of course, let me explain...\n456: Thank you, that was helpful.\n",
                "123: I'm glad I could assist.\n789: I have another question.\n123: Sure, ask away.\n"
            ],
            [
                ("456: I have a question about the new feature", "123: Sure, what do you need help with?"),
                ("789: Can you provide more details about the feature?", "123: Of course, let me explain..."),
                ("999: Another random message from me.", "123: I'm glad I could assist."),
                ("789: I have another question.", "123: Sure, ask away.")
            ]
        )
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=cutoff_days)).timestamp()

    validate_target_users(target_users, slack_user_id)
    # TODO: Join all channels where the user is a member
    # For now just join the specific channel the slash command is called
    # join_user_channels(slack_user_id, client)
    channel_id = command["channel_id"]
    client.conversations_join(channel=channel_id)
    cursor = None
    threads: List[str] = []
    while True:
        result = client.conversations_history(channel=channel_id, oldest=cutoff, cursor=cursor, limit=1000)
        for message in result["messages"]:
            # TODO: Only threaded messages will be scrapped for now
            if "reply_count" in message and message["reply_count"] > 0:
                threads.append(message["ts"])

        if not result["has_more"]:
            break

        cursor = result["response_metadata"]["next_cursor"]

    chat_transcript: List[str] = []
    chat_pairs: List[Tuple[str, str]] = []
    last_input = ""
    last_input_user = ""
    for ts in threads:
        result = client.conversations_replies(channel=channel_id, ts=ts, limit=1000)
        messages = result["messages"]
        messages.sort(key=lambda m: m["ts"])

        for message in messages:
            if "user" not in message or "text" not in message:
                continue

            user = message["user"]
            text = f"{user}: {message['text']}\n"

            if is_interacted_with_target(user, target_users, slack_user_id):
                if user != slack_user_id and last_input and last_input_user == slack_user_id:
                    chat_pairs.append((last_input, text))
                chat_transcript.append(text)
                last_input = text
                last_input_user = user

    if len(chat_transcript) < MIN_SCRAPED_THRESHOLD:
        logger.info(f"Chat history for {slack_user_id} is too short.")
        return None
    response = update_chat_pairs(chat_transcript, chat_pairs, slack_user_id, team_id)
    return chat_transcript, chat_pairs    


def get_chat_pairs(slack_user_id, team_id):
    slack_chat_pairs = get_chat_pairs(slack_user_id, team_id)
    return slack_chat_pairs