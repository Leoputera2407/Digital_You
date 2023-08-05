import json
import asyncio
from typing import Union, Pattern, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from slack_bolt.async_app import (
    AsyncAck,
    AsyncBoltContext,
)
from slack_sdk.web.async_client import AsyncWebClient

from digital_twin.config.app_config import MIN_CHAT_PAIRS_THRESHOLD
from digital_twin.slack_bot.personality import async_handle_user_conversation_style, async_rephrase_response
from digital_twin.slack_bot.views import (
    create_selection_command_view, 
    create_response_command_view, 
    create_general_text_command_view,
    ERROR_TEXT,
)
from digital_twin.slack_bot.utils import retrieve_sorted_past_messages
from digital_twin.qa import async_get_default_backend_qa_model
from digital_twin.db.async_slack_bot import async_get_chat_pairs
from digital_twin.db.user import (
    async_get_qdrant_collection_for_slack,
    async_get_typesense_collection_for_slack,
)
from digital_twin.db.engine import get_async_session
from digital_twin.search.interface import async_retrieve_hybrid_reranked_documents
from digital_twin.search.utils import chunks_to_search_docs
from digital_twin.indexdb.qdrant.store import QdrantVectorDB
from digital_twin.indexdb.typesense.store import TypesenseIndex
from digital_twin.indexdb.chunking.models import IndexChunk

from digital_twin.utils.slack import format_openai_to_slack
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time
logger = setup_logger()


async def async_gather_preprocess_tasks(
        async_db_session: AsyncSession, 
        client: AsyncWebClient, 
        context: AsyncBoltContext,
        slack_user_id: str,
        team_id: str, 
        view_id: str,
) -> List[str]:
    preprocess_tasks = {
        "conversation_style": async_handle_user_conversation_style(async_db_session, client, context, slack_user_id, team_id, view_id),
        "qdrant_collection_name": async_get_qdrant_collection_for_slack(async_db_session, slack_user_id, team_id),
        "typesense_collection_name": async_get_typesense_collection_for_slack(async_db_session, slack_user_id, team_id),
    }
    results = await asyncio.gather(*preprocess_tasks.values(), return_exceptions=True)
    for task_name, result in zip(preprocess_tasks.keys(), results):
        if isinstance(result, Exception):
            raise Exception(f"Error in {task_name} coroutine: {result}")
    return results

async def qa_and_response(
    query: str,
    channel_id: str,
    team_id: str,
    view_id: str,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    slack_user_id: str,
    thread_ts: Optional[str],
    ts: Optional[str],
) -> None:
    """
    This function synthesizes an AI generated response based on the query provided. 

    Parameters:
    query (str): The query to generate response.
    channel_id (str): The channel id where the command is triggered.
    team_id (str): The team id where the command is triggered.
    view_id (str): The id of the view to update.
    client (AsyncWebClient): The async Slack client to be used.
    ranked_chunks (List[Document], optional): List of documents ranked by relevance to the query.
    thread_ts (str, optional): The thread timestamp of the message to be updated.
    ts (str, optional): The timestamp of the message to be updated.

    Returns:
    None: This function doesn't return anything but updates the view with the AI generated response.
    """

    async with get_async_session() as async_db_session:
        conversation_style, qdrant_collection_name, typesense_collection_name = await async_gather_preprocess_tasks(
            async_db_session,
            client,
            context,
            slack_user_id,
            team_id,
            view_id
        )
        slack_chat_pairs = await async_get_chat_pairs(async_db_session, slack_user_id, team_id)

    is_using_default_conversation_style = False
    if len(slack_chat_pairs) < MIN_CHAT_PAIRS_THRESHOLD:
        is_using_default_conversation_style = True
    ranked_chunks, _ = await async_retrieve_hybrid_reranked_documents(
        query = query,
        user_id = None, # This mean it'll retrieve all public docs (which only that now)
        filters = None,
        vectordb = QdrantVectorDB(collection=qdrant_collection_name),
        keywordb = TypesenseIndex(collection=typesense_collection_name),
    )

    search_docs = chunks_to_search_docs(ranked_chunks)
    if len(search_docs) == 0:
        private_metadata_str = json.dumps(
            {
                "response": "Cannot find any relevant documents. Please ask a different question!"
            }
        ) 
        display_doc_view = create_response_command_view( 
                private_metadata_str=private_metadata_str,
                is_using_default_conversation_style=is_using_default_conversation_style,
                is_rephrasing_stage=False,
                search_docs=search_docs,
        )
        await client.views_update(view_id=view_id, view=display_doc_view)
        return

    private_metadata_str = json.dumps(
        {
            "response": "Synthezing AI generated response..."
        }
    ) 
    display_doc_view = create_response_command_view(
            private_metadata_str=private_metadata_str,
            is_using_default_conversation_style=is_using_default_conversation_style,
            is_rephrasing_stage=False,
            search_docs=search_docs,
    )
    await client.views_update(view_id=view_id, view=display_doc_view)

    qa_model = await async_get_default_backend_qa_model(model_timeout=10)
    qa_response, sources, is_docs_revelant, confidence_score = await qa_model.async_answer_question_and_verify(
        query, 
        context_docs=ranked_chunks,
    )
        
    processed_response = format_openai_to_slack(qa_response if qa_response else "")
    private_metadata_str = json.dumps(
        {
            "response": processed_response, 
            "channel_id": channel_id,
            "conversation_style": conversation_style,
            "is_docs_revelant": is_docs_revelant,
            "confidence_score": confidence_score,
        }
    )
    response_view = create_response_command_view(
        private_metadata_str=private_metadata_str, 
        is_using_default_conversation_style=is_using_default_conversation_style,
        is_rephrasing_stage=True,
        is_rephrase_answer_available=False,
        search_docs=search_docs,
    )
    await client.views_update(view_id=view_id, view=response_view)

    
    rephrased_response = await async_rephrase_response(
        conversation_style=conversation_style,
        query=query,
        slack_user_id=slack_user_id,
        qa_response=qa_response,
        chat_pairs=slack_chat_pairs,
    )
    private_metadata_str = json.dumps(
        {
            "response": processed_response, 
            "rephrased_response": rephrased_response,
            "channel_id": channel_id,
            "conversation_style": conversation_style,
            "is_docs_revelant": is_docs_revelant,
            "confidence_score": confidence_score,
            'is_using_default_conversation_style': is_using_default_conversation_style,
            'ts': thread_ts if thread_ts else ts,
        }
    )
    response_view = create_response_command_view(
        private_metadata_str=private_metadata_str,
        is_using_default_conversation_style=is_using_default_conversation_style,
        is_rephrasing_stage=True,
        is_rephrase_answer_available=True,
        search_docs=search_docs,
    )
    await client.views_update(view_id=view_id, view=response_view)
    return

@log_function_time()
async def handle_prosona_command(
    context: AsyncBoltContext,
    ack: AsyncAck,
    command: Union[str, Pattern],
    client: AsyncWebClient,
) -> None:
    await ack()
    slack_user_id = command["user_id"]
    channel_id = command["channel_id"]
    channel_name = command['channel_name']
    view_id = context["view_id"]
    try: 
        # Get the latest message from the channel
        past_messages = await retrieve_sorted_past_messages(
            client=client, 
            channel_id=channel_id, 
            context=context,
            limit_scanned_messages=5,
        )
        if not past_messages:
            error_view = create_general_text_command_view(
                text="Cannot find any messages in the channel. Please try again later!"
            )
            await client.views_update(view_id=view_id, view=error_view)
            return

        # NOTE: Due to the async interaction of slack actions, i.e. button clicks,
        # we need to handle the qa in the slack action handler.
        # Please refer to the `handle_selection_button` for the continuation of the qa

        # We need to parcel all the necessary metadata into the private_metadata field
        # Remember there's a 3000 word limit.
        private_metadata_str = json.dumps({
            "channel_id": channel_id,
        })
        # Create the selection modal view and open it
        selection_view = create_selection_command_view(
            past_messages=past_messages,
            private_metadata_str=private_metadata_str,
            in_thread=False,
        )
        await client.views_update(view_id=view_id, view=selection_view)
        return
    except Exception as e:
        logger.error(f"Error handling Prosona for {slack_user_id}: {e}")
        logger.info(f"The view_id is {view_id}")
        error_view = create_general_text_command_view(text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)
        return
