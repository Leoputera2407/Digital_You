import re 
import time 

from slack_sdk.web import WebClient
from slack_bolt import BoltContext
from typing import Optional, List
from postgrest.exceptions import APIError 

from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


def get_slack_supabase_user(slack_id: str, team_id: str) -> Optional[str]:
    data = get_slack_user(slack_id, team_id)
    return data.user_id if data else None


def insert_slack_supabase_user(slack_user_id: str, team_id: str, supabase_user_id: str) -> Optional[dict]:
    try:
        supabase = get_supabase_client()
        response = supabase.table('slack_users').insert({
            'slack_user_id': slack_user_id,
            'team_id': team_id,
            'user_id': supabase_user_id
        }).execute()
        if len(response.data) == 0:
            logger.error(f"Error inserting the user: {response}")
            raise Exception("Error inserting the user")
        return response

    except APIError as e:
        logger.error(f"Supabase Error: {str(e)}")
        return None

def get_vectordb_collection_for_slack(slack_user_id: str, team_id: str) -> str:
    """
    Get vectordb collection from the users table by joining on user_id with slack_users table 
    using the given slack_user_id and team_id

    Args:
    slack_user_id: The slack user id.
    team_id: The team id.

    Returns:
    The vectordb collection as string.

    Raises:
    Exception: If no user is found for the provided parameters.
    """
    try:
        response = get_supabase_client().table('slack_users').select(
            'users(qdrant_collection_key)'
        ).eq(
            'slack_user_id', slack_user_id
        ).eq(
            'team_id', team_id
        ).single().execute()

        if len(response.data) == 0:
            raise Exception(f"No user found for slack_user_id={slack_user_id} and team_id={team_id}")

        qdrant_collection_key = response.data['users']['qdrant_collection_key']

        return qdrant_collection_key
    except APIError as e:
        logger.error(f"Error fetching vectordb collection for slack_user_id={slack_user_id} and team_id={team_id}: {str(e)}")
        raise Exception(f"Supabase Error: {str(e)}")

def retrieve_sorted_past_messages(
    client: WebClient, 
    context: BoltContext,
    thread_ts: Optional[str]= None, # Not in thread if None
    limit_scanned_messages: int = 1000,
) -> List[str]:
    past_messages = client.conversations_history(
        channel=context.channel_id,
        include_all_metadata=True,
        ts=thread_ts,
        limit=limit_scanned_messages,
    ).get("messages", [])

    # Sort messages by timestamp, in ascending order
    past_messages.sort(key=lambda m: m["ts"])

    return past_messages

def get_the_last_messages_in_thread(
    sorted_past_messages: List[str],
    time_in_seconds: Optional[int] = 86400, # Last 24 hours
) -> List[str]:
    messages = []
    # Filter old messages by timestamp (in seconds)
    for message in sorted_past_messages:
        seconds = time.time() - float(message.get("ts"))
        if seconds < time_in_seconds:
            messages.append(message)

    return messages


# Conversion from Slack mrkdwn to OpenAI markdown
# See also: https://api.slack.com/reference/surfaces/formatting#basics
def slack_to_markdown(content: str) -> str:
    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for part in parts:
        if part.startswith("```") or part.startswith("`"):
            result += part
        else:
            for o, n in [
                (r"\*(?!\s)([^\*\n]+?)(?<!\s)\*", r"**\1**"),  # *bold* to **bold**
                (r"_(?!\s)([^_\n]+?)(?<!\s)_", r"*\1*"),  # _italic_ to *italic*
                (r"~(?!\s)([^~\n]+?)(?<!\s)~", r"~~\1~~"),  # ~strike~ to ~~strike~~
            ]:
                part = re.sub(o, n, part)
            result += part
    return result


# Conversion from OpenAI markdown to Slack mrkdwn
# See also: https://api.slack.com/reference/surfaces/formatting#basics
def markdown_to_slack(content: str) -> str:
    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for part in parts:
        if part.startswith("```") or part.startswith("`"):
            result += part
        else:
            for o, n in [
                (
                    r"\*\*\*(?!\s)([^\*\n]+?)(?<!\s)\*\*\*",
                    r"_*\1*_",
                ),  # ***bold italic*** to *_bold italic_*
                (
                    r"(?<![\*_])\*(?!\s)([^\*\n]+?)(?<!\s)\*(?![\*_])",
                    r"_\1_",
                ),  # *italic* to _italic_
                (r"\*\*(?!\s)([^\*\n]+?)(?<!\s)\*\*", r"*\1*"),  # **bold** to *bold*
                (r"__(?!\s)([^_\n]+?)(?<!\s)__", r"*\1*"),  # __bold__ to *bold*
                (r"~~(?!\s)([^~\n]+?)(?<!\s)~~", r"~\1~"),  # ~~strike~~ to ~strike~
            ]:
                part = re.sub(o, n, part)
            result += part
    return result


# Format message from Slack to send to OpenAI
def format_slack_to_openai(content: str) -> str:
    if content is None:
        return None

    # Unescape &, < and >, since Slack replaces these with their HTML equivalents
    # See also: https://api.slack.com/reference/surfaces/formatting#escaping
    content = content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    # Convert from Slack mrkdwn to markdown format
    content = slack_to_markdown(content)

    return content

# Format OpenAI to display in Slack
def format_openai_to_slack(content: str) -> str:
    for o, n in [
        # Remove leading newlines
        ("^\n+", ""),
        # Remove prepended Slack user ID
        ("^<@U.*?>\\s?:\\s?", ""),
        # Remove OpenAI syntax tags since Slack doesn't render them in a message
        ("```\\s*[Rr]ust\n", "```\n"),
        ("```\\s*[Rr]uby\n", "```\n"),
        ("```\\s*[Ss]cala\n", "```\n"),
        ("```\\s*[Kk]otlin\n", "```\n"),
        ("```\\s*[Jj]ava\n", "```\n"),
        ("```\\s*[Gg]o\n", "```\n"),
        ("```\\s*[Ss]wift\n", "```\n"),
        ("```\\s*[Oo]objective[Cc]\n", "```\n"),
        ("```\\s*[Cc]\n", "```\n"),
        ("```\\s*[Cc][+][+]\n", "```\n"),
        ("```\\s*[Cc][Pp][Pp]\n", "```\n"),
        ("```\\s*[Cc]sharp\n", "```\n"),
        ("```\\s*[Mm][Aa][Tt][Ll][Aa][Bb]\n", "```\n"),
        ("```\\s*[Jj][Ss][Oo][Nn]\n", "```\n"),
        ("```\\s*[Ll]a[Tt]e[Xx]\n", "```\n"),
        ("```\\s*bash\n", "```\n"),
        ("```\\s*zsh\n", "```\n"),
        ("```\\s*sh\n", "```\n"),
        ("```\\s*[Ss][Qq][Ll]\n", "```\n"),
        ("```\\s*[Pp][Hh][Pp]\n", "```\n"),
        ("```\\s*[Pp][Ee][Rr][Ll]\n", "```\n"),
        ("```\\s*[Jj]ava[Ss]cript\n", "```\n"),
        ("```\\s*[Ty]ype[Ss]cript\n", "```\n"),
        ("```\\s*[Pp]ython\n", "```\n"),
    ]:
        content = re.sub(o, n, content)

    # Convert from OpenAI markdown to Slack mrkdwn format
    content = markdown_to_slack(content)

    return content