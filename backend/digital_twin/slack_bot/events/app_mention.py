import time
import re

from openai.error import Timeout
from slack_bolt import App, Ack, BoltContext, BoltResponse
from slack_bolt.request.payload_utils import is_event
from slack_sdk.web import WebClient

from digital_twin.utils.logging import setup_logger
from digital_twin.utils.slack import format_slack_to_openai, format_openai_to_slack


logger = setup_logger()

def respond_to_app_mention(
    context: BoltContext,
    payload: dict,
    client: WebClient,
):
    # TODO: Ask Hamish if we should make our app mentioned able, 
    #       if we go down this route, we need to supply our own API KEY
    #       as the UX makes no sense, anyone in the workspace can @bot
    # We'll only react to app mentions in channels (i.e new convo), 
    # with no threads
    if payload.get("thread_ts") is not None:
        return
    try:
        messages = []
        # Strip bot Slack user ID from initial message, so we can format it to openai
        msg_text = re.sub(f"<@{context.bot_user_id}>\\s*", "", payload["text"])
        messages.append(
            f"<@{context.bot_user_id}>: " + format_slack_to_openai(msg_text)
        )

        # TODO: StuffQA 
       
    except Exception as e:
        text = f":warning: Failed to get an AI Response, try again later: {e}"
        logger.exception(text, e)
        client.chat_postEphemeral(
            channel=context.channel_id,
            text=text, 
            thread_ts=payload["ts"]
        )
