from typing import Optional, List, Tuple, Pattern, Union
from langchain.chat_models import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from slack_sdk.web.async_client import AsyncWebClient

from digital_twin.llm.interface import get_llm
from digital_twin.llm.chains.personality_chain import (
    RephraseChain,
    PersonalityChain, 
    NULL_DOC_TOKEN,
    PERSONALITY_MODEL_SETTINGS
) 
from digital_twin.slack_bot.views import get_view, PERSONALITY_TEXT
from digital_twin.slack_bot.scrape import scrape_and_store_chat_history
from digital_twin.utils.logging import setup_logger
from digital_twin.db.async_slack_bot import async_get_convo_style, async_update_convo_style

logger = setup_logger()


async def async_generate_and_store_user_conversation_style(
    session: AsyncSession, 
    slack_user_id: str, 
    team_id: str,
    chat_pairs: Optional[List[Tuple[str, str]]]
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
    personality_chain = PersonalityChain(
        llm=get_llm(
            **PERSONALITY_MODEL_SETTINGS
        ),
        max_output_tokens=PERSONALITY_MODEL_SETTINGS["max_output_tokens"],
    )

    # Generate personality description
    personality_description = await personality_chain.async_run(
        examples=chat_pairs,
        slack_user_id=slack_user_id,
    )
    res = await async_update_convo_style(session, personality_description, slack_user_id, team_id)
    if res is False:
        raise Exception(f"Error updating conversation style for {slack_user_id}")
    return personality_description


async def async_handle_user_conversation_style(
        db_session: AsyncSession,
        client: AsyncWebClient, 
        command: Union[str, Pattern], 
        slack_user_id: str, 
        team_id: str,
        view_id: str,
) -> str:
    try:
        conversation_style = await async_get_convo_style(
            db_session,
            slack_user_id, 
            team_id
        )
        if conversation_style is None:
            personality_view = get_view(
                "text_command_modal", text=PERSONALITY_TEXT)
            await client.views_update(view_id=view_id, view=personality_view)
            _, chat_pairs = await scrape_and_store_chat_history(
                db_session,
                command,
                slack_user_id,
                team_id,
                client
            )
            conversation_style = await async_generate_and_store_user_conversation_style(
                db_session,
                slack_user_id, 
                team_id, 
                chat_pairs,
            )
    except Exception as e:
        logger.error(
            f"Error getting user's conversation style for {slack_user_id}: {e}")
        raise Exception(
            f"Error getting user's conversation style for {slack_user_id}: {e}")

    return conversation_style


async def async_rephrase_response(
        chat_pairs: Optional[List[Tuple[str, str]]], 
        conversation_style: str,
        query: str, 
        slack_user_id: str, 
        qa_response: str,
) -> str :
    # We'll pass our own model here, with our own custom key
    # TODO: Figure out how to do this better
    try:
        rephrase_chain = RephraseChain(
            llm=get_llm(
                **PERSONALITY_MODEL_SETTINGS
            ),
            # Does nothign for now
            max_output_tokens=PERSONALITY_MODEL_SETTINGS["max_output_tokens"],
        )
        response = await rephrase_chain.async_run(
            examples=chat_pairs,
            conversation_style=conversation_style,
            query=query,
            slack_user_id=slack_user_id,
            document=qa_response if qa_response else NULL_DOC_TOKEN,
        )
        return response
    except Exception as e:
        logger.error(f"Error rephrasing response for {slack_user_id}: {e}")
        raise Exception(f"Error rephrasing response for {slack_user_id}: {e}")
