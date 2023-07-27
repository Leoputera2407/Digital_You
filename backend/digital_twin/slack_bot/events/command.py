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
from digital_twin.slack_bot.views import get_view,  ERROR_TEXT
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
        slack_user_id: str,
        team_id: str, 
        view_id: str,
) -> List[str]:
    preprocess_tasks = {
        "conversation_style": async_handle_user_conversation_style(async_db_session, client, slack_user_id, team_id, view_id),
        "slack_chat_pairs": async_get_chat_pairs(async_db_session, slack_user_id, team_id),
        "qdrant_collection_name": async_get_qdrant_collection_for_slack(async_db_session, slack_user_id, team_id),
        "typesense_collection_name": async_get_typesense_collection_for_slack(async_db_session, slack_user_id, team_id),
    }
    results = await asyncio.gather(*preprocess_tasks.values(), return_exceptions=True)
    for task_name, result in zip(preprocess_tasks.keys(), results):
        if isinstance(result, Exception):
            raise Exception(f"Error in {task_name} coroutine: {result}")
    return results


def temp_solution_create_collection_if_not_exist(
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

async def qa_and_response(
    query: str,
    channel_id: str,
    conversation_style: str,
    view_id: str,
    qdrant_collection_name: str,
    typesense_collection_name: str,
    client: AsyncWebClient,
    is_using_default_conversation_style: bool,
    slack_user_id: str,
    slack_chat_pairs: list[tuple[str, str]] = [],
    ranked_chunks: List[IndexChunk]=None
) -> None:
    """
    This function synthesizes an AI generated response based on the query provided. 

    Parameters:
    query (str): The query to generate response.
    channel_id (str): The channel id where the command is triggered.
    conversation_style (str): The style of conversation to be used.
    view_id (str): The id of the view to update.
    qdrant_collection_name (str): The collection name of the Qdrant DB.
    typesense_collection_name (str): The collection name of the Typesense DB.
    client (AsyncWebClient): The async Slack client to be used.
    is_using_default_conversation_style (bool): Flag to determine if default conversation style is being used.
    ranked_chunks (List[Document], optional): List of documents ranked by relevance to the query.

    Returns:
    None: This function doesn't return anything but updates the view with the AI generated response.
    """
    if not ranked_chunks:
        temp_solution_create_collection_if_not_exist(qdrant_collection_name, typesense_collection_name)

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
        display_doc_view = get_view(
                "response_command_modal", 
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
    display_doc_view = get_view(
            "response_command_modal", 
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
        add_metadata=False,
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
    response_view = get_view(
        "response_command_modal", 
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
        }
    )
    response_view = get_view(
        "response_command_modal",
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
    payload: dict[str, any], 
    command: Union[str, Pattern],
    client: AsyncWebClient,
) -> None:
    await ack()
    slack_user_id = command["user_id"]
    team_id = command["team_id"]
    channel_id = command["channel_id"]
    view_id = context["view_id"]

    try: 
        async with get_async_session() as async_db_session:
            conversation_style, slack_chat_pairs, qdrant_collection_name, typesense_collection_name = await async_gather_preprocess_tasks(
                async_db_session,
                client,
                slack_user_id,
                team_id,
                view_id
            )

        is_using_default_conversation_style = False
        if len(slack_chat_pairs) < MIN_CHAT_PAIRS_THRESHOLD:
            is_using_default_conversation_style = True
        

        thread_ts = payload.get("thread_ts")
        if thread_ts is None:
            limit_scanned_messages = 5
        else:
            limit_scanned_messages = 15
        # Get the latest message from the channel
        past_messages = await retrieve_sorted_past_messages(
            client, 
            context, 
            thread_ts=thread_ts, 
            limit_scanned_messages=limit_scanned_messages
        )
        if thread_ts is None:
            # NOTE: Due to the async interaction of slack actions, i.e. button clicks,
            # we need to handle the qa in the slack action handler.
            # Please refer to the `handle_selection_button` for the continuation of the qa

            # We need to parcel all the necessary metadata into the private_metadata field
            # Remember there's a 3000 word limit.
            private_metadata_str = json.dumps({
                "channel_id": channel_id,
                "conversation_style": conversation_style,
                "qdrant_collection_name": qdrant_collection_name,
                "typesense_collection_name": typesense_collection_name,
                "is_using_default_conversation_style": is_using_default_conversation_style,
                "slack_chat_pairs": slack_chat_pairs[:3],  # Give just 3 examples since space is limited
            })
            # Create the selection modal view and open it
            selection_view = get_view(
                "selection_command_modal", 
                past_messages=past_messages,
                private_metadata_str=private_metadata_str,
            )
            await client.views_update(view_id=view_id, view=selection_view)
            return

        else:
            # Construct the text with the format "user: message"
            text = "\n".join([f"{m['user']}: {m['text']}" for m in past_messages[-5:]])

            text_view = get_view("text_command_modal", text=text)
            await client.views_update(view_id=view_id, view=text_view)
            query = text
            await qa_and_response(
                slack_user_id=slack_user_id,
                query=query,
                channel_id=channel_id,
                conversation_style=conversation_style,
                view_id=view_id,
                qdrant_collection_name=qdrant_collection_name,
                typesense_collection_name=typesense_collection_name,
                client=client,
                is_using_default_conversation_style=is_using_default_conversation_style,
                slack_chat_pairs=slack_chat_pairs[:3],  # Give just 3 examples since space is limited
            )
            return   
    except Exception as e:
        logger.error(f"Error handling Prosona for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal", text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)
        return
