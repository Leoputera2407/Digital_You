from datetime import datetime, timezone
from typing import List, Optional, Tuple

from slack_bolt.async_app import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import NUM_SLACK_CHAT_PAIRS_TO_SHOW, SLACK_DAYS_TO_RESCRAPE
from digital_twin.config.constants import DEFAULT_SLACK_CONVERSATION_STYLE
from digital_twin.db.async_slack_bot import async_get_convo_style_and_last_update_at, async_update_convo_style
from digital_twin.llm.chains.personality_chain import (
    NULL_DOC_TOKEN,
    PERSONALITY_MODEL_SETTINGS,
    PersonalityChain,
    RephraseChain,
)
from digital_twin.llm.interface import get_llm
from digital_twin.slack_bot.scrape import scrape_and_store_chat_history_from_dm
from digital_twin.slack_bot.utils import view_update_with_appropriate_token
from digital_twin.slack_bot.views import PERSONALITY_TEXT, create_general_text_command_view
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


async def async_generate_and_store_user_or_default_conversation_style(
    session: AsyncSession,
    slack_user_id: str,
    team_id: str,
    chat_pairs: Optional[List[Tuple[str, str]]],
) -> Optional[str]:
    """
    This function generates and stores the conversation style of a user.

    It processes chat pairs to format the chat history, then uses an instance of the PersonalityChain class to
    generate a personality description. The description is then updated in a supabase table named 'slack_users' for the
    given slack_user_id and team_id.

    Parameters:
    - slack_user_id: str
        The slack ID of the user.

    - team_id: str
        The ID of the team to which the user belongs.

    - chat_pairs: Optional[List[Tuple[str, str]]]
        The pairs of messages in the conversation. Each pair consists of two messages represented as strings. If None,
        it is assumed that there are no chat pairs to process.

    Returns:
    None or string of conversation style description.
    """
    if chat_pairs is not None:
        personality_chain = PersonalityChain(
            llm=get_llm(
                temperature=PERSONALITY_MODEL_SETTINGS["temperature"],
                max_output_tokens=int(PERSONALITY_MODEL_SETTINGS["max_output_tokens"]),
            ),
        )
        # Generate personality description

        personality_description = await personality_chain.async_run(
            examples=chat_pairs,
            slack_user_id=slack_user_id,
        )
    else:
        personality_description = DEFAULT_SLACK_CONVERSATION_STYLE
    res = await async_update_convo_style(session, personality_description, slack_user_id, team_id)
    if res is False:
        raise Exception(f"Error updating conversation style for {slack_user_id}")
    return personality_description


async def async_handle_user_conversation_style(
    db_session: AsyncSession,
    client: AsyncWebClient,
    slack_user_token: str,
    slack_user_id: str,
    view_slack_token: str,
    team_id: str,
    view_id: str,
) -> str:
    try:
        conversation_style, updated_at = await async_get_convo_style_and_last_update_at(
            db_session, slack_user_id, team_id
        )
        if conversation_style is None or (
            updated_at is not None
            and (datetime.now(timezone.utc) - updated_at).days >= SLACK_DAYS_TO_RESCRAPE
        ):
            personality_view = create_general_text_command_view(
                text=PERSONALITY_TEXT,
            )
            await view_update_with_appropriate_token(
                client=client, view=personality_view, view_id=view_id, view_slack_token=view_slack_token
            )
            _, chat_pairs = await scrape_and_store_chat_history_from_dm(
                db_session,
                slack_user_id,
                team_id,
                client,
                slack_user_token,
            )
            conversation_style = await async_generate_and_store_user_or_default_conversation_style(
                db_session,
                slack_user_id,
                team_id,
                chat_pairs,
            )
    except Exception as e:
        logger.error(f"Error getting user's conversation style for {slack_user_id}: {e}")
        raise Exception(f"Error getting user's conversation style for {slack_user_id}: {e}")

    return conversation_style


async def async_rephrase_response(
    chat_pairs: Optional[List[Tuple[str, str]]],
    conversation_style: str,
    query: str,
    slack_user_id: str,
    qa_response: str,
) -> str:
    try:
        filter_chat_pairs = chat_pairs[:NUM_SLACK_CHAT_PAIRS_TO_SHOW] if chat_pairs else []
        rephrase_chain = RephraseChain(
            llm=get_llm(
                temperature=PERSONALITY_MODEL_SETTINGS["temperature"],
                max_output_tokens=int(PERSONALITY_MODEL_SETTINGS["max_output_tokens"]),
            ),
        )
        response = await rephrase_chain.async_run(
            examples=filter_chat_pairs,
            conversation_style=conversation_style,
            query=query,
            slack_user_id=slack_user_id,
            document=qa_response if qa_response else NULL_DOC_TOKEN,
        )
        return response
    except Exception as e:
        logger.error(f"Error rephrasing response for {slack_user_id}: {e}")
        raise Exception(f"Error rephrasing response for {slack_user_id}: {e}")
