import json
import asyncio
from typing import Union, Pattern, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from slack_bolt.async_app import (
    AsyncAck,
    AsyncBoltContext,
)
from slack_sdk.web.async_client import AsyncWebClient
from langchain.chat_models import ChatOpenAI

from digital_twin.config.app_config import PERSONALITY_CHAIN_API_KEY
from digital_twin.llm.chains.verify_chain import StuffVerify
from digital_twin.llm.chains.personality_chain import NULL_DOC_TOKEN
from digital_twin.slack_bot.personality import async_handle_user_conversation_style, async_rephrase_response
from digital_twin.slack_bot.views import get_view, LOADING_TEXT, ERROR_TEXT
from digital_twin.slack_bot.utils import retrieve_sorted_past_messages
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.db.async_slack_bot import async_get_chat_pairs
from digital_twin.db.user import (
    async_get_qdrant_collection_for_slack,
    async_get_typesense_collection_for_slack,
)
from digital_twin.db.engine import get_async_session
from digital_twin.search.interface import async_retrieve_hybrid_reranked_documents
from digital_twin.indexdb.qdrant.store import QdrantVectorDB
from digital_twin.indexdb.typesense.store import TypesenseIndex

from digital_twin.utils.logging import setup_logger
logger = setup_logger()


class NoChatPairsException(Exception):
    pass


async def async_gather_preprocess_tasks(
        async_db_session: AsyncSession, 
        client: AsyncWebClient, 
        command: Union[str, Pattern], 
        slack_user_id: str,
        team_id: str, 
        view_id: str,
) -> List[str]:
    preprocess_tasks = {
        "conversation_style": async_handle_user_conversation_style(async_db_session, client, command, slack_user_id, team_id, view_id),
        "slack_chat_pairs": async_get_chat_pairs(async_db_session, slack_user_id, team_id),
        "qdrant_collection_name": async_get_qdrant_collection_for_slack(async_db_session, slack_user_id, team_id),
        "typesense_collection_name": async_get_typesense_collection_for_slack(async_db_session, slack_user_id, team_id),
    }
    results = await asyncio.gather(*preprocess_tasks.values(), return_exceptions=True)
    for task_name, result in zip(preprocess_tasks.keys(), results):
        if isinstance(result, Exception):
            raise Exception(f"Error in {task_name} coroutine: {result}")
    return results


async def async_verify_if_docs_are_relevant(
        query: str,
        context: List[InferenceChunk],
) -> Optional[bool]:
    
    # TODO: Make this more portable 
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        openai_api_key=PERSONALITY_CHAIN_API_KEY,
        temperature=0,
        # About 300 words
        max_tokens=500,
    )

    verify_chain = StuffVerify(
        llm=llm,
        max_output_tokens=500,
    )
    res = await verify_chain.async_run(
        query,
        context
    )
    if "yes" in res.lower():
        return True
    elif "no" in res.lower():
        return False
    else:
        return None

def temp_sol_create_collection_if_not_exist(
        qdrant_collection_name: str, 
        typesense_collection_name: str
) -> None:
    from digital_twin.indexdb.qdrant.indexing import (
        create_collection,
        list_collections,
    )
    from digital_twin.indexdb.typesense.store import (
        check_typesense_collection_exist,
        create_typesense_collection,
    )
    
    if qdrant_collection_name not in {
        collection.name for collection in list_collections().collections
    }:
        logger.info(
            f"Creating collection with name: {qdrant_collection_name}"
        )
        create_collection(collection_name=qdrant_collection_name)
    
    if not check_typesense_collection_exist(typesense_collection_name):
        logger.info(
            f"Creating Typesense collection with name: {typesense_collection_name}"
        )
        create_typesense_collection(collection_name=typesense_collection_name)

async def handle_digital_twin_command(
    context: AsyncBoltContext,
    ack: AsyncAck,
    command: Union[str, Pattern],
    client: AsyncWebClient
) -> None:
    await ack()
    slack_user_id = command["user_id"]
    team_id = command["team_id"]
    channel_id = command["channel_id"]
    trigger_id = command['trigger_id']
    loading_view = get_view("text_command_modal", text=LOADING_TEXT)
    response = await client.views_open(trigger_id=trigger_id, view=loading_view)
    view_id = response["view"]["id"]

    try:
        # Get the latest message from the channel
        past_messages = await retrieve_sorted_past_messages(client, context, thread_ts=None, limit_scanned_messages=1)
        query = past_messages[0]["text"]

        async with get_async_session() as async_db_session:
            conversation_style, slack_chat_pairs, qdrant_collection_name, typesense_collection_name = await async_gather_preprocess_tasks(
                async_db_session,
                client,
                command,
                slack_user_id,
                team_id,
                view_id
            )

        # Raise an exception if there's no chat history
        if len(slack_chat_pairs) == 0:
            raise NoChatPairsException(
                f"Can't find enough chat history in threads or DMs.")
        
        temp_sol_create_collection_if_not_exist(qdrant_collection_name, typesense_collection_name)
       
        ranked_chunks, _ = await async_retrieve_hybrid_reranked_documents(
            query = query,
            user_id = None, # This mean it'll retrieve all public docs (which only that now)
            filters = None,
            vectordb = QdrantVectorDB(collection=qdrant_collection_name),
            keywordb = TypesenseIndex(collection=typesense_collection_name),
        )  

        res = await async_verify_if_docs_are_relevant(query, ranked_chunks)
        logger.info(f"res: {res}")
        
        response = await async_rephrase_response(slack_chat_pairs, conversation_style, query, slack_user_id, {NULL_DOC_TOKEN})
        private_metadata_str = json.dumps(
            {"response": response, "channel_id": channel_id,
                "query": query, "conversation_style": conversation_style}
        )
        response_view = get_view(
            "response_command_modal", private_metadata_str=private_metadata_str, response=response)
        await client.views_update(view_id=view_id, view=response_view)
        return
    except NoChatPairsException as e:
        logger.error(f"Error handling Prosona for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal",
                              text=f"Something went wrong, {e}. ")
        await client.views_update(view_id=view_id, view=error_view)
        return
    except Exception as e:
        logger.error(f"Error handling Prosona for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal", text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)
        return
