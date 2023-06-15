from postgrest.exceptions import APIError

from typing import Optional, List, Tuple
from langchain.chat_models import ChatOpenAI


from digital_twin.config.app_config import PERSONALITY_CHAIN_API_KEY
from digital_twin.qa.personality_chain import RephraseChain, PersonalityChain, NULL_DOC_TOKEN
from digital_twin.slack_bot.views import get_view, PERSONALITY_TEXT
from digital_twin.slack_bot.scrape import scrape_and_store_chat_history
from digital_twin.utils.logging import setup_logger
from digital_twin.db.slack_bot import get_convo_style, update_convo_style

logger = setup_logger()


def get_user_conversation_style(slack_user_id: str, team_id: str) -> Optional[str]:
    """Get conversation style from slack_users table for the 
    given slack_user_id and team_id.
    
    If found on table, return the conversation style.
    Else, return None.
    """
    data = get_convo_style(slack_user_id, team_id)
    if data is None:
        return None
    else:
        return data['conversation_style']


def generate_and_store_user_conversation_style(slack_user_id: str, team_id: str, chat_pairs: Optional[List[Tuple[str, str]]]) -> Optional[str]:
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
    # We'll pass our own model here, with our own custom key
    # TODO: Figure out how to do this better
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        openai_api_key=PERSONALITY_CHAIN_API_KEY,
        temperature=0,
        # About 300 words
        max_tokens=500,
    )

    personality_chain = PersonalityChain(
        llm=llm,
        # Does nothing for now
        max_output_tokens=4096,
    )

    # Generate personality description
    personality_description = personality_chain(
        examples=chat_pairs,
        slack_user_id=slack_user_id,
    )
    data = update_convo_style(personality_description, slack_user_id, team_id)

    return personality_description


def handle_user_conversation_style(client, command, slack_user_id, team_id, view_id):
    try:
        conversation_style = get_user_conversation_style(slack_user_id, team_id)
        if conversation_style is None:
            personality_view = get_view("text_command_modal", text=PERSONALITY_TEXT)
            client.views_update(view_id=view_id, view=personality_view)
            _, chat_pairs = scrape_and_store_chat_history(
                command,
                slack_user_id, 
                team_id, 
                client
            )
            conversation_style = generate_and_store_user_conversation_style(slack_user_id, team_id, chat_pairs)
    except Exception as e:
        logger.error(f"Error getting user's conversation style for {slack_user_id}: {e}")
        raise Exception(f"Error getting user's conversation style for {slack_user_id}: {e}")

    return conversation_style



def rephrase_response(chat_pairs, conversation_style, query, slack_user_id, qa_response):
    # We'll pass our own model here, with our own custom key
    # TODO: Figure out how to do this better
    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=PERSONALITY_CHAIN_API_KEY,
            temperature=0,
            # About 300 words
            max_tokens=500,
        )
        rephrase_chain = RephraseChain(
            llm=llm,
            # Does nothign for now
            max_output_tokens=4096,
        )
        response = rephrase_chain(
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