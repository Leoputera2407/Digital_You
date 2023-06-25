from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import MIN_SCRAPED_THRESHOLD, MIN_CHAT_PAIRS_THRESHOLD
from digital_twin.utils.logging import setup_logger
from digital_twin.db.async_slack_bot import async_update_chat_pairs

logger = setup_logger()

def validate_target_users(
        target_users: Optional[List[str]], 
        slack_user_id: str
) -> None:
    if target_users is not None:
        if slack_user_id in target_users and len(target_users) == 1:
            raise ValueError("target_users cannot only contain the slack_user_id")

def is_interacted_with_target(
        user: str, 
        target_users: Optional[List[str]],
        slack_user_id: str
) -> bool:
    return target_users is None or user in target_users or user == slack_user_id

async def join_user_channels(
        slack_user_id: str, 
        client: AsyncWebClient
) -> List[str]:
    # Get the list of channels where the user is a member
    response = await client.users_conversations(user=slack_user_id, types="public_channel,private_channel", exclude_archived=True)
    
    channel_ids = []
    for channel in response["channels"]:
        # Join the channel
        await client.conversations_join(channel=channel["id"])
        channel_ids.append(channel["id"])

    return channel_ids

async def scrape_and_store_chat_history(
        db_session: AsyncSession,
        slack_user_id: str, 
        team_id: str, 
        client: AsyncWebClient, 
        target_users: Optional[List[str]]= None, 
        min_message_length: int = MIN_SCRAPED_THRESHOLD, 
        min_chat_pairs_len: int = MIN_CHAT_PAIRS_THRESHOLD,
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
   
    channel_ids = await join_user_channels(slack_user_id, client)
    chat_transcript: List[str] = []
    chat_pairs: List[Tuple[str, str]] = []
    last_input = ""
    last_input_user = ""
    for channel_id in channel_ids:
        cursor = None
        threads: List[str] = []
        while True:
            result = await client.conversations_history(channel=channel_id, oldest=cutoff, cursor=cursor, limit=1000)
            for message in result["messages"]:
                # TODO: Only threaded messages will be scrapped for now
                if "reply_count" in message and message["reply_count"] > 0:
                    threads.append(message["ts"])

            if not result["has_more"]:
                break

            cursor = result["response_metadata"]["next_cursor"]
  
        for ts in threads:
            result = await client.conversations_replies(channel=channel_id, ts=ts, limit=1000)
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

    if len(chat_transcript) < min_message_length or len(chat_pairs) < min_chat_pairs_len:
        logger.info(f"Chat history for {slack_user_id} is too short. Chat_transcript: {len(chat_transcript)}, Chat_pairs: {len(chat_pairs)}")
        return None, None
    
    slack_user = await async_update_chat_pairs(db_session, chat_transcript, chat_pairs, slack_user_id, team_id)
    if slack_user is None:
        logger.info(f"Failed to update chat history for {slack_user_id}.")
        return None, None
    return chat_transcript, chat_pairs