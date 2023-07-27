from typing import List, Optional, Dict

from slack_bolt.async_app import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

async def retrieve_sorted_past_messages(
    client: AsyncWebClient, 
    context: AsyncBoltContext,
    thread_ts: Optional[str]= None, # Not in thread if None
    limit_scanned_messages: int = 1000,
) -> List[Dict[str, str]]:
    # Join the channel
    await client.conversations_join(
        channel=context.channel_id,
    )
    messages = await client.conversations_history(
        channel=context.channel_id,
        include_all_metadata=True,
        ts=thread_ts,
        limit=limit_scanned_messages,
    )
    
    past_messages = messages.get("messages", [])
    # Filter only user messages
    past_messages = [m for m in past_messages if m.get('subtype') is None]

    # Sort messages by timestamp, in ascending order
    past_messages.sort(key=lambda m: m["ts"])

    # Create a list of dictionaries containing required fields
    past_messages_dict = []
    for m in past_messages:
        # Get user info
        user_info = await client.users_info(user=m.get('user'))
        user_display_name = user_info.get('user', {}).get('profile', {}).get('real_name_normalized', '')
        past_messages_dict.append({'message': m.get('text'), 'thread_ts': m.get('thread_ts'), 'sender': user_display_name})

    return past_messages_dict
