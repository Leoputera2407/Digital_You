from typing import List, Optional
import ast
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error
from digital_twin.db.model import APIKey, ModelConfig
from digital_twin.server.model import APIKeyBase, BaseModelConfig

logger = setup_logger()

@log_supabase_api_error(logger)
def get_slack_user(slack_id, team_id):
    supabase = get_supabase_client()
    response = supabase.table('slack_users').select('*').eq(
        'slack_user_id', slack_id).eq('team_id', team_id).single().execute()
    return response


@log_supabase_api_error(logger)
def insert_slack_user(slack_user_id, team_id, supabase_user_id):
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

@log_supabase_api_error(logger)
def get_qdrant_key(slack_user_id, team_id):
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
