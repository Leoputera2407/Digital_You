import json
from slack_sdk import WebClient
from slack_bolt.context import BoltContext

from digital_twin.qa.personality_chain import NULL_DOC_TOKEN
from digital_twin.slack_bot.scrape import get_chat_pairs
from digital_twin.slack_bot.personality import handle_user_conversation_style, rephrase_response
from digital_twin.slack_bot.views import get_view, LOADING_TEXT, ERROR_TEXT
from digital_twin.utils.slack import get_vectordb_collection_for_slack, retrieve_sorted_past_messages
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

class NoChatPairsException(Exception):
    pass

def handle_digital_twin_command(context: BoltContext, ack, command, client: WebClient):
    ack()
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

        conversation_style = handle_user_conversation_style(client, command, slack_user_id, team_id, view_id)
        slack_chat_pairs = get_chat_pairs(slack_user_id, team_id)
        if len(slack_chat_pairs) == 0:
            raise NoChatPairsException(f"Can't find enough chat history in threads or DMs.")
        collection = get_vectordb_collection_for_slack(slack_user_id, team_id)
        """
        docs = retrieve_documents(
            query, filters=None, vectordb=create_datastore(collection)
        )
        # If relevant docs were found, do the qa chain
        qa_response = handle_qa_response(supabase_user_id, slack_user_id, query, docs)
        """
        response = rephrase_response(slack_chat_pairs, conversation_style, query, slack_user_id, {NULL_DOC_TOKEN})
        private_metadata_str = json.dumps(
            {"response": response, "channel_id": channel_id, "query": query, "conversation_style": conversation_style}
        )
        response_view = get_view("response_command_modal", private_metadata_str=private_metadata_str, response=response)
        client.views_update(view_id=view_id, view=response_view)
        return
    except NoChatPairsException as e:
        logger.error(f"Error handling digital twin for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal", text=f"Something went wrong, {e}. ")
        client.views_update(view_id=view_id, view=error_view)
        return 
    except Exception as e:
        logger.error(f"Error handling digital twin for {slack_user_id}: {e}")
        error_view = get_view("text_command_modal", text=ERROR_TEXT)
        client.views_update(view_id=view_id, view=error_view)
        return 
    
    