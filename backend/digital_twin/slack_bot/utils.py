from typing import Dict, List, Optional

from slack_sdk.web.async_client import AsyncWebClient

from digital_twin.slack_bot.defs import VIEW_TYPE, ChannelType


async def retrieve_sorted_past_messages(
    client: AsyncWebClient,
    channel_id: str,
    channel_type: str,
    thread_ts: Optional[str] = None,  # Not in thread if None
    limit_scanned_messages: int = 1000,
) -> List[Dict[str, str]]:
    # Join the channel if it's not a direct message
    if channel_type == ChannelType.PUBLIC_CHANNEL.value:
        await client.conversations_join(
            channel=channel_id,
        )

    if thread_ts is not None:
        # Fetch messages from the thread
        messages = await client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=limit_scanned_messages,
        )
    else:
        # Fetch messages from the channel
        messages = await client.conversations_history(
            channel=channel_id,
            include_all_metadata=True,
            limit=limit_scanned_messages,
        )

    past_messages = messages.get("messages", [])
    # Filter only user messages
    past_messages = [m for m in past_messages if m.get("subtype") is None]

    # Sort messages by timestamp, in ascending order
    past_messages.sort(key=lambda m: m["ts"])

    # Create a list of dictionaries containing required fields
    past_messages_dict = []
    for m in past_messages:
        # Get user info
        user_info = await client.users_info(user=m.get("user"))
        user_display_name = user_info.get("user", {}).get("profile", {}).get("real_name_normalized", "")
        past_messages_dict.append(
            {
                "message": m.get("text"),
                "thread_ts": m.get("thread_ts"),
                "ts": m.get("ts"),
                "sender": user_display_name,
            }
        )

    return past_messages_dict


def format_source_type(source_type: str) -> str:
    words = source_type.split("_")
    capitalized_words = [word.capitalize() for word in words]
    return " ".join(capitalized_words)


async def view_update_with_appropriate_token(
    client: AsyncWebClient, view: VIEW_TYPE, view_id: str, view_slack_token: str
):
    original_client_token = client.token
    client.token = view_slack_token
    await client.views_update(view_id=view_id, view=view)
    client.token = original_client_token
    return
