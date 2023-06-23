from typing import List, Optional

from slack_bolt.async_app import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient


async def retrieve_sorted_past_messages(
    client: AsyncWebClient, 
    context: AsyncBoltContext,
    thread_ts: Optional[str]= None, # Not in thread if None
    limit_scanned_messages: int = 1000,
) -> List[str]:
    messages = await client.conversations_history(
        channel=context.channel_id,
        include_all_metadata=True,
        ts=thread_ts,
        limit=limit_scanned_messages,
    )
    
    past_messages = messages.get("messages", [])

    # Sort messages by timestamp, in ascending order
    past_messages.sort(key=lambda m: m["ts"])

    return past_messages