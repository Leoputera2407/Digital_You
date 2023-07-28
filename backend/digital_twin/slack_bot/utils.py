from typing import List, Optional, Dict

from slack_bolt.async_app import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

async def retrieve_sorted_past_messages(
    client: AsyncWebClient, 
    channel_id: str,
    thread_ts: Optional[str]= None, # Not in thread if None
    limit_scanned_messages: int = 1000,
) -> List[Dict[str, str]]:
    # Join the channel
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
    past_messages = [m for m in past_messages if m.get('subtype') is None]

    # Sort messages by timestamp, in ascending order
    past_messages.sort(key=lambda m: m["ts"])

    # Create a list of dictionaries containing required fields
    past_messages_dict = []
    for m in past_messages:
        # Get user info
        user_info = await client.users_info(user=m.get('user'))
        user_display_name = user_info.get('user', {}).get('profile', {}).get('real_name_normalized', '')
        past_messages_dict.append(
            {
                'message': m.get('text'), 
                'thread_ts': m.get('thread_ts'), 
                'ts': m.get('ts'),
                'sender': user_display_name
            }
        )

    return past_messages_dict
