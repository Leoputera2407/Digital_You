
from slack_sdk import WebClient
from slack_bolt.context import BoltContext

from digital_twin.qa.personality_chain import NULL_DOC_TOKEN
from digital_twin.slack_bot.scrape import get_chat_pairs
from digital_twin.slack_bot.personality import handle_user_conversation_style, rephrase_response
from digital_twin.slack_bot.views import open_command_modal, update_command_modal_text, update_command_modal_response
from digital_twin.utils.slack import get_vectordb_collection_for_slack, retrieve_sorted_past_messages
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def handle_digital_twin_command(context: BoltContext, ack, command, client: WebClient):
    ack()
    slack_user_id = command["user_id"]
    team_id = command["team_id"]
    channel_id = command["channel_id"]
    trigger_id = command['trigger_id']
    view_id = open_command_modal(client, trigger_id)

    try:  
        # Get the latest message from the channel
        past_messages = retrieve_sorted_past_messages(client, context, thread_ts= None, limit_scanned_messages = 1)
        query = past_messages[0]["text"]

        conversation_style = handle_user_conversation_style(client, command, slack_user_id, team_id, view_id)
        slack_chat_pairs = get_chat_pairs(slack_user_id, team_id)
        collection = get_vectordb_collection_for_slack(slack_user_id, team_id)
        """
        docs = retrieve_documents(
            query, filters=None, vectordb=create_datastore(collection)
        )
        # If relevant docs were found, do the qa chain
        qa_response = handle_qa_response(supabase_user_id, slack_user_id, query, docs)
        """
        response = rephrase_response(slack_chat_pairs, conversation_style, query, slack_user_id, {NULL_DOC_TOKEN})
        update_command_modal_response(client, channel_id, view_id, response, query)
        return
    except Exception as e:
        logger.error(f"Error handling digital twin for {slack_user_id}: {e}")
        update_command_modal_text(
            client,
            view_id,
            "Something went wrong. Please try again later."
        )
        return 
    
    