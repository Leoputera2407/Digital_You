import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from slack_bolt.async_app import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import MIN_CHAT_PAIRS_THRESHOLD, MIN_SCRAPED_THRESHOLD
from digital_twin.db.async_slack_bot import async_update_chat_pairs
from digital_twin.slack_bot.defs import ChannelType
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


def validate_target_users(target_users: Optional[List[str]], slack_user_id: str) -> None:
    if target_users is not None:
        if slack_user_id in target_users and len(target_users) == 1:
            raise ValueError("target_users cannot only contain the slack_user_id")


def is_interacted_with_target(user: str, target_users: Optional[List[str]], slack_user_id: str) -> bool:
    return target_users is None or user in target_users or user == slack_user_id


def is_user_message(message):
    required_keys = ["client_msg_id", "type", "text", "user", "ts"]

    return (
        message.get("type") == "message"
        and all(key in message for key in required_keys)
        and message.get("blocks")
        and len(message["blocks"]) > 0
        and message["blocks"][0].get("type") == "rich_text"
        and message["blocks"][0].get("elements")
        and len(message["blocks"][0]["elements"]) > 0
        and message["blocks"][0]["elements"][0].get("type") == "rich_text_section"
    )


async def join_user_channels(
    slack_user_id: str,
    client: AsyncWebClient,
    channel_types: Optional[List[ChannelType]] = None,
) -> List[str]:
    if channel_types is None:
        raise ValueError("channel_types must be provided")

    types_to_include = ",".join(channel_type.value for channel_type in channel_types)
    # Get the list of channels where the user is a member
    response = await client.users_conversations(
        user=slack_user_id, types=types_to_include, exclude_archived=True
    )
    channel_ids = []
    for channel in response["channels"]:
        if "is_im" in channel and channel["is_im"]:  # If it's a DM, no need to join
            channel_ids.append(channel["id"])
        else:
            # Join the channel if it's not a DM
            await client.conversations_join(channel=channel["id"])
            channel_ids.append(channel["id"])

    return channel_ids


async def _scrape(
    client: AsyncWebClient,
    channel_ids: List[str],
    target_users: Optional[List[str]],
    slack_user_id: str,
    num_messages: int,
    is_dm: bool,
    cutoff_days: int = 365,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Scrape the user's past interactions in Slack threads and store them in the Supabase database.
    We'll only see `contiguous` interactions between slack_user_id and target_users.
    If target_users is None, then slack_user_id and all other users are considered.
    Caveat -- We only scrape messages inside threads, and not messages in channels.

    Args:
        slack_user_id (str): The Slack user ID for whom to scrape the chat history.
        team_id (str): The ID of the Slack team/channel from which to scrape the chat history.
        client (WebClient): The WebClient instance for making API calls to the Slack API.
        target_users (List[str]): List of Slack user IDs considered as target users ie people we want them to talk to.
        num_messages (int): Number of messages to scrape.
        is_dm (bool): Whether the channel is a DM channel or not.
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
    # To avoid circular imports
    from digital_twin.utils.slack import format_slack_to_openai

    # cutoff = (datetime.now(timezone.utc) - timedelta(days=cutoff_days)).timestamp()
    chat_transcript: List[str] = []
    chat_pairs: List[Tuple[str, str]] = []
    last_input = ""
    last_input_user = ""

    for channel_id in channel_ids:
        cursor = None
        while True:
            result = await client.conversations_history(channel=channel_id, cursor=cursor, limit=num_messages)
            messages = result["messages"]

            # If this is a DM, handle non-threaded messages first
            if is_dm:
                for message in messages:
                    if not is_user_message(message):  # Skip non-user messages
                        continue

                    if "reply_count" not in message or message["reply_count"] == 0:
                        user = message["user"]
                        formatted_text = format_slack_to_openai(message["text"])
                        text = f"{user}: {formatted_text}\n"
                        if user != slack_user_id and last_input and last_input_user == slack_user_id:
                            chat_pairs.append((last_input, text))
                        chat_transcript.append(text)
                        last_input = text
                        last_input_user = user
                break

            # Handle threaded messages (for both DMs and regular channels)
            for message in messages:
                if "reply_count" in message and message["reply_count"] > 0:
                    thread_result = await client.conversations_replies(
                        channel=channel_id, ts=message["ts"], limit=1000
                    )
                    thread_messages = thread_result["messages"]

                    for thread_message in thread_messages:
                        user = thread_message["user"]
                        formatted_text = format_slack_to_openai(thread_message["text"])
                        text = f"{user}: {formatted_text}\n"

                        if is_interacted_with_target(user, target_users, slack_user_id):
                            if user != slack_user_id and last_input and last_input_user == slack_user_id:
                                chat_pairs.append((last_input, text))
                            chat_transcript.append(text)
                            last_input = text
                            last_input_user = user

            if not result["has_more"]:
                break

            cursor = result["response_metadata"]["next_cursor"]
    # shuffle, so ordering doesn't matter
    random.shuffle(chat_pairs)
    return chat_transcript, chat_pairs


async def scrape_and_store_chat_history_from_channels(
    db_session: AsyncSession,
    slack_user_id: str,
    team_id: str,
    client: AsyncWebClient,
    num_channels: Optional[int] = None,
    target_channels: Optional[List[str]] = None,
    target_users: Optional[List[str]] = None,
    min_transcript_length: int = MIN_SCRAPED_THRESHOLD,
    min_chat_pairs_len: int = MIN_CHAT_PAIRS_THRESHOLD,
    cutoff_days: int = 365,
) -> Tuple[List[str] | None, List[Tuple[str, str]] | None]:
    validate_target_users(target_users, slack_user_id)
    channel_ids = await join_user_channels(
        slack_user_id,
        client,
        channel_types=[ChannelType.PUBLIC_CHANNEL],
    )
    if target_channels is not None:
        channel_ids = [channel_id for channel_id in channel_ids if channel_id in target_channels]
    if num_channels is not None:
        channel_ids = channel_ids[:num_channels]
    chat_transcript, chat_pairs = await _scrape(
        client=client,
        channel_ids=channel_ids,
        target_users=target_users,
        slack_user_id=slack_user_id,
        num_messages=1000,
        cutoff_days=cutoff_days,
        is_dm=False,
    )

    if len(chat_transcript) < min_transcript_length or len(chat_pairs) < min_chat_pairs_len:
        logger.info(
            f"Chat history for {slack_user_id} is too short. Chat_transcript: {len(chat_transcript)}, Chat_pairs: {len(chat_pairs)}"
        )
        return None, None
    slack_user = await async_update_chat_pairs(
        db_session, chat_transcript, chat_pairs, slack_user_id, team_id
    )
    if slack_user is None:
        logger.info(f"Failed to update chat history for {slack_user_id}.")
        return None, None
    return chat_transcript, chat_pairs


async def scrape_and_store_chat_history_from_dm(
    db_session: AsyncSession,
    slack_user_id: str,
    team_id: str,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    target_users: Optional[List[str]] = None,
    min_transcript_length: int = MIN_SCRAPED_THRESHOLD,
    min_chat_pairs_len: int = MIN_CHAT_PAIRS_THRESHOLD,
    cutoff_days: int = 365,
) -> Tuple[List[str] | None, List[Tuple[str, str]] | None]:
    # We need to ensure that we use slack_user_token
    # to scrape the DMs
    default_token = client.token
    client.token = context["SLACK_USER_TOKEN"]

    validate_target_users(target_users, slack_user_id)
    channel_ids = await join_user_channels(
        slack_user_id,
        client,
        channel_types=[ChannelType.DM],
    )
    chat_transcript, chat_pairs = await _scrape(
        client=client,
        channel_ids=channel_ids,
        target_users=target_users,
        slack_user_id=slack_user_id,
        num_messages=50,
        cutoff_days=cutoff_days,
        is_dm=True,
    )

    if len(chat_transcript) < min_transcript_length or len(chat_pairs) < min_chat_pairs_len:
        logger.info(
            f"Chat history for {slack_user_id} is too short. Chat_transcript: {len(chat_transcript)}, Chat_pairs: {len(chat_pairs)}"
        )
        return None, None

    slack_user = await async_update_chat_pairs(
        db_session, chat_transcript, chat_pairs, slack_user_id, team_id
    )

    # Switch back to default token
    client.token = default_token

    if slack_user is None:
        logger.info(f"Failed to update chat history for {slack_user_id}.")
        return None, None
    return chat_transcript, chat_pairs
