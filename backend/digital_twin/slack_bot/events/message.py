import logging
import time

from typing import List, Optional
from slack_bolt import  BoltContext
from slack_sdk.web import WebClient

from digital_twin.utils.slack import (
    format_slack_to_openai, 
    format_openai_to_slack,
    retrieve_sorted_past_messages,
    get_the_last_messages_in_thread,
)


def is_bot_in_thread(
    context: BoltContext,
    past_messages: List[str],
) -> bool:
    bot_user_id = context.bot_id  # assuming this is how you retrieve the bot's user_id
    #slack_user_id = context.actor_user_id or context.user_id
    for message in past_messages:
        if message.get('user') in [bot_user_id]:
            return True
    return False

def respond_to_new_message(
    context: BoltContext,
    payload: dict,
    client: WebClient,
    logger: logging.Logger,
):
    if payload.get("bot_id") is not None and payload.get("bot_id") != context.bot_id:
        # Skip a new message by a different app
        return
    
    try:
        is_in_dm_with_bot = payload.get("channel_type") == "im"
        thread_ts = payload.get("thread_ts")
        if not is_in_dm_with_bot or thread_ts is not None:
            # We only support direct convo in DMs
            return
        """ # TODO: Decide if we want to want to support bot talking in public channels
        is_user_or_bot_mentioned_in_thread = False
        if is_in_dm_with_bot is False and thread_ts is None:
            # We only support DM or if the bot had messaged is in a thread
            return
        """  
        messages_in_context = []
        if is_in_dm_with_bot is True and thread_ts is None:
            # In the DM with the bot

            # Get the last messages in a day
            past_messages_in_channel = retrieve_sorted_past_messages(
                client, context, thread_ts=None, limit_scanned_messages=100
            )
            
            messages_in_context.extend(get_the_last_messages_in_thread(
                past_messages_in_channel, time_in_seconds=86400
            ))
        """ # TODO: Decide if we want to want to support bot talking in public channels
        else:
            # In a thread with the bot in a channel

            past_messages_in_thread = retrieve_sorted_past_messages(
                client, context, thread_ts=thread_ts, limit_scanned_messages=1000
            )
            messages_in_context.extend(past_messages_in_thread)

            is_user_or_bot_mentioned_in_thread = is_user_or_bot_mentioned_in_thread(
                payload, context, past_messages_in_thread
            )
        
        # TODO: Decide if we want to include user in threads check
        if not is_in_dm_with_bot and not is_bot_in_thread:
            # We only support DMs with Bot or
            # if bot is mentioned in a thread
            return
        """
        if len(messages_in_context) == 0:
            return

        messages = []
        for reply in messages_in_context:
            msg_user_id = reply.get("user")
            reply_text = reply.get("text")
            messages.append(f"<@{msg_user_id}>: "+ format_slack_to_openai(reply_text))

        openai_api_key = context.get("OPENAI_API_KEY")
        # TODO: Call StuffChain
        # return format_openai_to_slack(response)
    except Exception as e:
        logger.exception("Failed to respond to a new message", e)
        client.chat_update(
            channel=context.channel_id,
            ts=payload["ts"],
            text=f":sad: Failed to reply: {e}",
        )
