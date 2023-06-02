import json

from uuid import uuid4
from datetime import datetime
from postgrest.exceptions import APIError
from typing import Optional

from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.state_store import OAuthStateStore
from slack_sdk.oauth.installation_store.models import Installation, Bot


from digital_twin.config.app_config import (
    SLACK_CLIENT_ID, 
    SLACK_CLIENT_SECRET, 
)
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

class BotTokenEncoder:
    @staticmethod
    def encode(bot_token_dict):
        encoded_dict = bot_token_dict.copy()

        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        encoded_dict = {key: convert_datetime(value) for key, value in encoded_dict.items()}

        return json.dumps(encoded_dict)

    @staticmethod
    def decode(encoded_json):
        decoded_dict = json.loads(encoded_json)

        datetime_keys = ["bot_token_expires_at", "user_token_expires_at", "installed_at"]

        class DateTimeDecoder(json.JSONDecoder):
            def __init__(self, *args, **kwargs):
                super().__init__(object_hook=self._datetime_hook, *args, **kwargs)

            @staticmethod
            def _datetime_hook(obj_dict):
                for key in datetime_keys:
                    if key in obj_dict and isinstance(obj_dict[key], str):
                        obj_dict[key] = datetime.fromisoformat(obj_dict[key])
                return obj_dict

        return DateTimeDecoder().decode(json.dumps(decoded_dict))


class SupabaseInstallationStore(InstallationStore):
    def save(self, installation: Installation):
        logger.info("We're being called here from installations.")
        # Encode bot_data into a JSON string
        bot_dict = installation.to_bot().to_dict()
        bot_dict_json = BotTokenEncoder.encode(bot_dict)
        bot_dict_decoded = json.loads(bot_dict_json)
        data = {
            'enterprise_id': installation.enterprise_id,
            'team_id': installation.team_id,
            'user_id': installation.user_id,
            'installed_at': bot_dict_decoded.get('installed_at'),
            'bot': bot_dict_json,
        } 
        try:
            get_supabase_client().table('slack_installations').insert(data).execute()
        except APIError as e:
            raise Exception(f"Supabase Error during installation save: {str(e)}")

    def find_installation(
        self,
        *,
        enterprise_id: Optional[str] = None,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        try:
            query = get_supabase_client().table('slack_installations').select('*')
            if enterprise_id:
                query = query.eq('enterprise_id', enterprise_id)
            if team_id:
                query = query.eq('team_id', team_id)
            if user_id:
                query = query.eq('user_id', user_id)

            response = query.order('installed_at', desc=True).execute()
        except APIError as e:
            raise Exception(f"Supabase Error during installation find: {str(e)}")
        
        if len(response.data) == 0:
          return None

        data = response.data[0]
        bot = BotTokenEncoder.decode(data['bot'])
        return Installation(
            app_id=bot['app_id'],
            user_id=data['user_id'],
            enterprise_id=bot['enterprise_id'],
            enterprise_name=bot['enterprise_name'],
            team_id=bot['team_id'],
            team_name=bot['team_name'],
            bot_token=bot['bot_token'],
            bot_id=bot['bot_id'],
            bot_user_id=bot['bot_user_id'],
            bot_scopes=bot['bot_scopes'],
            bot_refresh_token=bot['bot_refresh_token'],
            bot_token_expires_at=bot['bot_token_expires_at'],
            is_enterprise_install=bot['is_enterprise_install'],
            installed_at=bot['installed_at'].timestamp(),  # Convert datetime to timestamp
          )
 
          

    def delete_installation(self, *, enterprise_id: Optional[str], team_id: Optional[str], user_id: Optional[str]=None):
        try:
            get_supabase_client().table('slack_installations').delete().eq('enterprise_id', enterprise_id).eq('team_id', team_id).execute()
        except APIError as e:
            raise Exception(f"Supabase Error when deleting installations: {str(e)}")

    def save_bot(self, bot: Bot):
        bot_dict = BotTokenEncoder.encode(bot.to_dict())
        try:
            # Get existing bot data
            query = get_supabase_client().table('slack_bots').select('*').eq('team_id', bot.team_id)
            if bot.enterprise_id:
                query = query.eq('enterprise_id', bot.enterprise_id) 

            response = query.execute()
            
            if len(response.data) > 0:
                # Bot exists, so update the existing row
                get_supabase_client().table('slack_bots').update(bot_dict).eq('team_id', bot.team_id).eq('enterprise_id', bot.enterprise_id).execute()
            else:
                # Bot does not exist, so insert a new row

                get_supabase_client().table('slack_bots').insert(bot_dict).execute()
        except APIError as e:
            raise Exception(f"Supabase Error during bot save: {str(e)}")

    def find_bot(
        self, *, 
        enterprise_id: Optional[str], 
        team_id: Optional[str],   
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        try:
            query = get_supabase_client().table('slack_bots').select('*').eq('team_id', team_id)
            if enterprise_id:
                query = query.eq('enterprise_id', enterprise_id) 

            response = query.order('installed_at', desc=True).execute()
        except APIError as e:
            raise Exception(f"Supabase Error when finding bot: {str(e)}")
        
        rows = response.data
        if len(rows) == 0:
            return None

        data = json.loads(rows[0])  # Assuming only one bot per team
        return Bot(
            app_id=data['app_id'],
            enterprise_id=data['enterprise_id'],
            team_id=data['team_id'],
            bot_token=data['bot_token'],
            bot_refresh_token=data['bot_refresh_token'],
            bot_token_expires_at=data['bot_token_expires_at'],
            bot_id=data['bot_id'],
            bot_user_id=data['bot_user_id'],
            bot_scopes=data['bot_scopes'],
            installed_at=data['installed_at'].timestamp(),  # Convert datetime to timestamp
        )


    def delete_installation(self, *, enterprise_id: Optional[str], team_id: Optional[str], user_id: Optional[str]=None):
        try:
            query =get_supabase_client().table('slack_installations').delete()
            if enterprise_id:
                query = query.eq('enterprise_id', enterprise_id)
            if team_id:
                query = query.eq('team_id', team_id)
            if user_id:
                query = query.eq('user_id', user_id)
            query.execute()
        except APIError as e:
            raise Exception(f"Supabase Error when deleting installations: {str(e)}")

    
class SupabaseOAuthStateStore(OAuthStateStore):

    def issue(self) -> str:
        state = str(uuid4())
        try:
            get_supabase_client().table('slack_states').insert({'state': state}).execute()
        except APIError as e:
            raise Exception(f"Supabase Error when issue slack_states: {str(e)}")
        return state

    def consume(self, state: str) -> bool:
        try:
            response = get_supabase_client().table('slack_states').select('*').eq('state', state).execute()
            if len(response.data) == 0:
                return False
            get_supabase_client().table('slack_states').update({"consumed": True}).eq('state', state).execute()
        except APIError as e:
            raise Exception(f"Supabase Error when consuming oauth states: {str(e)}")

        return True

def get_oauth_settings():
    return OAuthSettings(
        client_id=SLACK_CLIENT_ID,
        client_secret=SLACK_CLIENT_SECRET,
        # TODO: Make this a app_config
        scopes=[
            "app_mentions:read",
            "channels:history",
            "channels:join",
            "channels:read",
            "chat:write",
            "chat:write.customize",
            "commands",
            "users.profile:read",
            "users:read",
        ],
        install_page_rendering_enabled=True,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        installation_store=SupabaseInstallationStore(),
        state_store=SupabaseOAuthStateStore(),
        logger=logger,
    )