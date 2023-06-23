import json
import asyncio
from typing import Union, Pattern
from slack_bolt.async_app import (
    AsyncAck, 
    AsyncRespond, 
    AsyncSay,
    AsyncAck,
    AsyncBoltContext,
)
from slack_sdk.web.async_client import AsyncWebClient

from digital_twin.llm.chains.personality_chain import NULL_DOC_TOKEN
from digital_twin.slack_bot.personality import async_handle_user_conversation_style, async_rephrase_response
from digital_twin.slack_bot.views import get_view, LOADING_TEXT, ERROR_TEXT
from digital_twin.utils.slack import retrieve_sorted_past_messages
from digital_twin.db.async_slack_bot import async_get_chat_pairs
from digital_twin.db.user import (
    async_get_qdrant_collection_by_user_id, 
    async_get_typesense_collection_by_user_id,
)
from digital_twin.db.engine import get_async_session

from digital_twin.utils.logging import setup_logger
logger = setup_logger()

class NoChatPairsException(Exception):
    pass

async def handle_digital_twin_command(
    context: AsyncBoltContext,
    ack: AsyncAck, 
    command: Union[str, Pattern], 
    client: AsyncWebClient
) -> None :
    await ack()
    slack_user_id = command["user_id"]
    team_id = command["team_id"]
    channel_id = command["channel_id"]
    trigger_id = command['trigger_id']
    loading_view = get_view("text_command_modal", text=LOADING_TEXT)
    response = client.views_open(trigger_id=trigger_id, view=loading_view)
    view_id = response["view"]["id"]

    try:  
        # Get the latest message from the channel
        past_messages = retrieve_sorted_past_messages(client, context, thread_ts= None, limit_scanned_messages = 1)
        query = past_messages[0]["text"]
        
        async with get_async_session() as async_db_session:  # Using the async session context manager
            # Schedule tasks to run concurrently and await for all of them to finish
            db_tasks  = {
                "conversation_style": async_handle_user_conversation_style(async_db_session, client, command, slack_user_id, team_id, view_id),
                "slack_chat_pairs": async_get_chat_pairs(async_db_session, slack_user_id, team_id),
                "qdrant_collection_name": async_get_qdrant_collection_by_user_id(async_db_session, slack_user_id),
                "typesense_collection_name": async_get_typesense_collection_by_user_id(async_db_session, slack_user_id),
            }
            results = await asyncio.gather(*db_tasks.values(), return_exceptions=True)
            for task_name, result in zip(db_tasks.keys(), results):
                if isinstance(result, Exception):
                    raise Exception(f"Error in {task_name}: {result}")
            

        conversation_style, slack_chat_pairs, qdrant_collection_name, typesense_collection_name = results

        # Raise an exception if there's no chat history
        if len(slack_chat_pairs) == 0:
            raise NoChatPairsException(f"Can't find enough chat history in threads or DMs.")
        """
        pueudo code:
        Async
        # check if there are any good doc
        verify_chain(supabase_user_id, slack_user_id, query, docs)
        
        # do a vector search
        vector_search_docs = retrieve_documents( 
            query, filters=None, vectordb=create_datastore(collection)        
            )    
        if len(vector_search_docs) == 0:
        # do a keyword search
        keyword_search_docs = search_keywords()
        # bring docs together
        all_results = await asyncio.gather(keyword_search_docs, vector_search_docs)  # parallel calls
        # Score the combination of the two - this is time expensive 
        rescore = cross_encoder_rescore(query, all_results)
        
        
        # If relevant docs were found, do the qa chain
        qa_response = handle_qa_response(supabase_user_id, slack_user_id, query, docs)
        """
        response = await async_rephrase_response(slack_chat_pairs, conversation_style, query, slack_user_id, {NULL_DOC_TOKEN})
        private_metadata_str = json.dumps(
            {"response": response, "channel_id": channel_id, "query": query, "conversation_style": conversation_style}
        )
        response_view = get_view("response_command_modal", private_metadata_str=private_metadata_str, response=response)
        await client.views_update(view_id=view_id, view=response_view)  
        return
    except NoChatPairsException as e:
        logger.error(f"Error handling Prosona for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal", text=f"Something went wrong, {e}. ")
        await client.views_update(view_id=view_id, view=error_view)
        return 
    except Exception as e:
        logger.error(f"Error handling Prosona for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal", text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)
        return 
    
    