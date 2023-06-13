from typing import List, Optional
import ast
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error
from digital_twin.db.model import APIKey, ModelConfig
from digital_twin.server.model import APIKeyBase, BaseModelConfig

logger = setup_logger()


@log_supabase_api_error(logger)
def delete_installations(enterprise_id: Optional[str], team_id: Optional[str]):
    supabase = get_supabase_client()
    response = supabase.table("slack_installations").delete().eq('enterprise_id', enterprise_id).eq('team_id', team_id).execute()
    data = response.data
    return data if data else None

@log_supabase_api_error(logger)
def insert_installations(data):
    supabase = get_supabase_client()
    response = supabase.table('slack_installations').insert(data).execute()
    return response

@log_supabase_api_error(logger)
def get_installations(enterprise_id, team_id, user_id):
    supabase = get_supabase_client()
    query = supabase.table('slack_installations').select('*')
    if enterprise_id:
        query = query.eq('enterprise_id', enterprise_id)
    if team_id:
        query = query.eq('team_id', team_id)
    if user_id:
        query = query.eq('user_id', user_id)

    response = query.order('installed_at', desc=True).execute()
    return response

@log_supabase_api_error(logger)
def get_bots(bot):
    supabase = get_supabase_client()
    query = supabase.table('slack_bots').select('*').eq('team_id', bot.team_id)
    if bot.enterprise_id:
        query = query.eq('enterprise_id', bot.enterprise_id) 
    response = query.execute()
    return response

@log_supabase_api_error(logger)
def update_bots(bot, bot_dict):
    supabase = get_supabase_client()
    query = supabase.table('slack_bots').update(bot_dict).eq('team_id', bot.team_id).eq('enterprise_id', bot.enterprise_id).execute()
    return query

@log_supabase_api_error(logger)
def insert_bot(bot_dict):
    supabase = get_supabase_client()
    query = supabase.table('slack_bots').insert(bot_dict).execute()
    return query

@log_supabase_api_error(logger)
def find_bot(enterprise_id, team_id):
    supabase = get_supabase_client()
    query = supabase.table('slack_bots').select('*').eq('team_id', team_id)
    if enterprise_id:
        query = query.eq('enterprise_id', enterprise_id) 

    response = query.order('installed_at', desc=True).execute()
    return response


@log_supabase_api_error(logger)
def delete_installs(enterprise_id: Optional[str], team_id: Optional[str], user_id: Optional[str]):
    supabase = get_supabase_client()
    query = supabase.table('slack_installations').delete()
    if enterprise_id:
        query = query.eq('enterprise_id', enterprise_id)
    if team_id:
        query = query.eq('team_id', team_id)
    if user_id:
        query = query.eq('user_id', user_id)
    response = query.execute()
    return response

@log_supabase_api_error(logger)
def insert_state(state):
    supabase = get_supabase_client()
    response = supabase.table('slack_states').insert({'state': state}).execute()
    data = response.data
    return data if data else None

@log_supabase_api_error(logger)
def get_and_update_state(state):
    supabase = get_supabase_client()
    response = supabase.table('slack_states').select('*').eq('state', state).execute()
    if len(response.data) == 0:
        return False
    supabase.table('slack_states').update({"consumed": True}).eq('state', state).execute()
    
@log_supabase_api_error(logger)
def get_convo_style(slack_user_id, team_id):
    supabase = get_supabase_client()
    response = supabase.table('slack_users').select('conversation_style').eq(
        'slack_user_id', slack_user_id).eq('team_id', team_id).single().execute()
    return response

    
@log_supabase_api_error(logger)
def update_convo_style(personality_description, slack_user_id, team_id):
    supabase = get_supabase_client()
    response = supabase.table('slack_users').update(
            {
                "conversation_style": personality_description
            }
        ).eq(
            'slack_user_id', slack_user_id
        ).eq(
            'team_id', team_id
        ).execute()
    return response

@log_supabase_api_error(logger)
def update_chat_pairs(chat_transcript, chat_pairs, slack_user_id, team_id):
    supabase = get_supabase_client()
    response = supabase.table('slack_users').update({
        "contiguous_chat_transcript": str(chat_transcript),
        "chat_pairs": str(chat_pairs),
    }).eq("slack_user_id", slack_user_id).eq("team_id", team_id).execute()
    return response

@log_supabase_api_error(logger)
def get_chat_pairs(slack_user_id, team_id):
    supabase = get_supabase_client()
    response = supabase.table('slack_users').select(
            'chat_pairs'
        ).eq(
            'slack_user_id', slack_user_id
        ).eq(
            'team_id', team_id
        ).single().execute()
    
    if len(response.data) == 0:
        logger.error(f"No data found for {slack_user_id} in 'slack_users' table.")
        return None

    interactions_str = response.data['chat_pairs']
    slack_chat_pairs = ast.literal_eval(interactions_str)
    return slack_chat_pairs
