import json

from uuid import UUID
from logging import Logger
from urllib.parse import urlencode
from typing import Dict, Any, Callable, Awaitable, Union
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as StarletteResponse, RedirectResponse

from slack_sdk.http_retry.builtin_async_handlers import AsyncRateLimitErrorRetryHandler
from slack_bolt import BoltResponse
from slack_bolt.error import BoltError
from slack_bolt.request.payload_utils import is_event, is_view, is_action
from slack_bolt.async_app import (
    AsyncApp, 
    AsyncAck, 
    AsyncAck,
    AsyncBoltContext,
)
from slack_sdk.web.async_client import AsyncWebClient
from slack_bolt.adapter.fastapi.async_handler import (
    AsyncSlackRequestHandler,
)
from slack_bolt.oauth.async_oauth_flow import AsyncOAuthFlow

from digital_twin.auth.users import current_user, current_admin_for_org
from digital_twin.llm.interface import get_llm
from digital_twin.config.app_config import WEB_DOMAIN, SLACK_USER_TOKEN
from digital_twin.slack_bot.views import LOADING_TEXT
from digital_twin.db.model import User
from digital_twin.db.engine import get_async_session, get_session
from digital_twin.llm.chains.personality_chain import ShuffleChain, PERSONALITY_MODEL_SETTINGS
from digital_twin.slack_bot.views import (
    get_view,
    ERROR_TEXT,
    MODAL_RESPONSE_CALLBACK_ID,
    EDIT_BUTTON_ACTION_ID,
    SHUFFLE_BUTTON_ACTION_ID,
    SELECTION_BUTTON_ACTION_ID,
    EDIT_BLOCK_ID,
)
from digital_twin.slack_bot.events.command import (
    handle_prosona_command,
    qa_and_response,
)
from digital_twin.slack_bot.events.home_tab import build_home_tab
from digital_twin.slack_bot.config import get_oauth_settings
from digital_twin.server.model import AuthUrl
from digital_twin.db.model import SlackUser
from digital_twin.db.engine import get_async_session_generator
from digital_twin.db.user import (
    async_get_slack_user, 
    async_get_user_by_email,
    async_insert_slack_user,
    async_get_organization_id_from_team_id,
)

from digital_twin.utils.slack import (
    SlackResponseStatus,
    to_starlette_response,
    custom_handle_slack_oauth_redirect,
    custom_handle_installation,
    format_openai_to_slack,
    format_slack_to_openai,
    async_get_user_info,
)
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
router = APIRouter()


MESSAGE_SUBTYPES_TO_SKIP = ["message_changed", "message_deleted"]
# To reduce unnecessary workload in this app,
# this before_authorize function skips message changed/deleted events.
# Especially, "message_changed" events can be triggered many times when the app rapidly updates its reply.
async def before_authorize(
    payload: Dict[str, Any], 
    body: Dict[str, Any], 
    next_: Callable[[], Awaitable[None]],
):
    if (
        (
            is_event(body)
            and payload.get("type") == "message"
            and payload.get("subtype") in MESSAGE_SUBTYPES_TO_SKIP
        )
        or (
            # this covers things like channel_join, channel_leave, etc.
            is_event(body)
            and payload.get("event", {}).get("subtype") is not None
        ) or (
            # this covers things like bot_message
            is_event(body)
            and payload.get("event", {}).get("bot_profile")
        )
    ):
        logger.debug(
            "Skipped the following middleware and listeners "
            f"for this message event (subtype: {payload.get('subtype')})"
        )
        return BoltResponse(status=200, body="")
    
    await next_()

slack_app = AsyncApp(
    oauth_settings=get_oauth_settings(),
    process_before_response=True,
    before_authorize=before_authorize,
)
slack_app.client.retry_handlers.append(AsyncRateLimitErrorRetryHandler(max_retry_count=2))

async def just_ack(ack: AsyncAck):
    await ack()

def register_listeners(slack_app: AsyncApp):
    #slack_app.event("app_mention")(ack=just_ack, lazy=[respond_to_app_mention])
    #slack_app.event("message")(ack=just_ack, lazy=[respond_to_new_message])
    slack_app.command("/prosona")(ack=just_ack, lazy=[handle_prosona_command])
    #slack_app.action(SHUFFLE_BUTTON_ACTION_ID)(ack=just_ack, lazy=[])
    #slack_app.view(MODAL_RESPONSE_CALLBACK_ID)(lazy=[])

register_listeners(slack_app)

app_handler = AsyncSlackRequestHandler(slack_app)

class SlackServerSignup(BaseModel):
    supabase_user_id: str
    team_id: str
    slack_user_id: str


@router.post("/slack/events")
async def handle_slack_event(req: Request):  
   return await app_handler.handle(req)

@router.get("/slack/install/{organization_id}")
async def install(
    response: StarletteResponse, 
    organization_id: UUID,
    request: Request,
    user: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> AuthUrl:
    oauth_flow: AsyncOAuthFlow = app_handler.app.oauth_flow
    if oauth_flow is not None and \
            request.method == "GET":
        logger.info(f"Handling slack install {organization_id}")

        bolt_resp = await custom_handle_installation(
            user=user,
            oauth_flow=oauth_flow,
            organization_id=organization_id,
            db_session=db_session,
            request=request,
        ) 
        # Convert bolt response to starlette response
        res = to_starlette_response(bolt_resp)
        
        # Extract state from the cookie
        cookie_header = res.headers.get('set-cookie', '')
        if "=" in cookie_header and ";" in cookie_header:
            state = cookie_header.split('=')[1].split(';')[0]
        else:
            logger.error("Invalid or missing 'set-cookie' header in response")
            raise HTTPException(status_code=500, detail="Internal server error")
            
        # Prepare the auth URL
        auth_url = res.body.decode()
        
        # Set cookies
        response.set_cookie(
            key='slack-app-oauth-state',
            value=state,
            samesite='None',
            secure=True,
            max_age=600,
        )
        return AuthUrl(auth_url=auth_url)
 
    return HTTPException(
            status_code=404,
            content="Slack Installation Request is malformed",
    )

@router.get("/slack/oauth_redirect")
async def slack_oauth_redirect(
    request: Request,
    db_session: AsyncSession = Depends(get_async_session_generator),
):
    """
    We want to attach a slack creds of the admin user who handled the installs.
    To connect slack_user and our user, we used the only common attribute they have
    which is email.

    One big assumption we have here is the email
    they used to register on slack is the same email that
    they used to register to our service. If this assumption is broken,
    this maybe a future cause of bug.

    We'll also create a connector credential for the admin user here too.
    """
    oauth_flow: AsyncOAuthFlow = app_handler.app.oauth_flow
    if oauth_flow is not None and \
        request.url.path == oauth_flow.redirect_uri_path and \
            request.method == "GET":
        res = await custom_handle_slack_oauth_redirect(
            oauth_flow=oauth_flow,
            db_session=db_session,
            request=request,
        )
        if isinstance(res, SlackResponseStatus):
            # If status code indicates success, redirect to the settings page
            if res.success: 
                return RedirectResponse(url=f"{WEB_DOMAIN}/settings/connectors")
            else:  # On failure, redirect to the WEB_DOMAIN with the status and body as query parameters
                error_data = {
                    'status': res.status_code,
                    'error_message': res.error_message,
                    'connector_type': 'slack'
                }
                return RedirectResponse(url=f"{WEB_DOMAIN}/settings/connectors?{urlencode(error_data)}")
            
        raise HTTPException(
            status_code=500, 
            detail="Unexpected response type from custom_handle_slack_oauth_redirect"
        )
    return StarletteResponse(
            status_code=404,
            content="Not found",
    )


@slack_app.event("url_verification")
async def handle_url_verification(body: Dict[str, Any]):
    challenge = body.get("challenge")
    return {"challenge": challenge}

@slack_app.middleware
async def set_user_info(
    context: AsyncBoltContext, 
    payload: Dict[str, Any], 
    body: Dict[str, Any], 
    next_: Callable[[], Awaitable[None]],
    client: AsyncWebClient,
) -> None:
    event_type = payload.get('event', {}).get('type', '')
    logger.info(f"Event type: {event_type}")
    if event_type == 'app_home_opened':
        next_()
    if is_action(body) or is_view(body):
        slack_user_id = body["user"]["id"]
        team_id = body["team"]["id"]
    else:
        slack_user_id = payload.get("user_id", '')
        team_id = payload.get("team_id", '')
    try:
        if not slack_user_id or not team_id:
            # Wierd edge-case, just in case we get a bad payload
            raise ValueError(f'Error while verifying the slack token')
        
        if 'command' in payload:
            trigger_id = payload['trigger_id']
            loading_view = get_view("text_command_modal", text=LOADING_TEXT)
            response = await client.views_open(trigger_id=trigger_id, view=loading_view)
            context["view_id"] = response["view"]["id"]
        # Look up user in external system using their Slack user ID
        async with get_async_session() as async_db_session: 
            organization_id = await async_get_organization_id_from_team_id(
                session=async_db_session,
                team_id=team_id,
            )
            if not organization_id:
                return BoltResponse(
                    status=200,
                    body="Your Slack Workspace is not associated to any Organization. Please contant your administrator.",
                )
            slack_user: SlackUser = await async_get_slack_user(async_db_session, slack_user_id, team_id)
            if slack_user is None:
                slack_user_info = await client.users_info(user=slack_user_id)
                slack_user_email = slack_user_info.get('user', {}).get('profile', {}).get('email', None) 
                if not slack_user_email:
                    raise ValueError(f'Error while verifying the slack token')
                db_user: User = await async_get_user_by_email(async_db_session, slack_user_email)
                if not db_user:
                    raise ValueError(f'Error while verifying the slack token')
                
                slack_user = await async_insert_slack_user(
                    async_db_session, 
                    slack_user_id, 
                    team_id, 
                    db_user.id
                )
                if not slack_user:
                    raise ValueError(f'Error while verifying the slack token') 
            context["DB_USER_ID"] = slack_user.user_id
            context["ORGANIZATION_ID"] = organization_id
    except Exception as e:
        logger.info(f"Error while verifying the slack token: {e}")
        return BoltResponse(status=200, body=f"Sorry <@{slack_user_id}>, you aren't registered for Prosona Service. Please sign up here <{WEB_DOMAIN} | Prosona Website>")
    
    await next_()

@slack_app.event("app_home_opened")
async def render_home_tab(
    client: AsyncWebClient, 
    context: AsyncBoltContext
) -> None:
    db_user_id = context.get("DB_USER_ID", None)
    if not db_user_id:
        slack_user_id = context.get("user_id", '')
        team_id = context.get("team_id", '')
        if not slack_user_id or not team_id:
            # Wierd edge-case, just in case we get a bad payload
            raise BoltError(f'Error while verifying the slack token')
        search_params = "?slack_user_id={slack_user_id}&team_id={team_id}"
        text = f"""
        To enable this app in this Slack workspace, you need to login to Prosona. "
        Visit <{WEB_DOMAIN}/interface/slack{search_params} | Prosona Website> to login."
        """
    else:
        text = "Welcome to Prosona!"

    await client.views_publish(
        user_id=context.user_id,
        view=build_home_tab(text),
    )


@slack_app.view(MODAL_RESPONSE_CALLBACK_ID)
async def handle_view_submission(
    ack: AsyncAck, 
    client: AsyncWebClient, 
    body: Dict[str, Any],
) -> None:
    await ack()

    payload: Dict[str, Any] = json.loads(body['view']['private_metadata'])
    channel_id = payload['channel_id']

     # Check if the submission is from the edit view
    if payload.get("source") == "edit":
        # Here, instead of using the original response from payload, 
        # get the updated response from the user's input
        response = body['view']['state']['values'][EDIT_BLOCK_ID]['response_input']['value']
    else:
        response = payload['rephrased_response']
        
    await client.chat_postMessage(
        channel=channel_id,
        text=response,
        username=body['user']['username'],
        token=SLACK_USER_TOKEN,
    )

@slack_app.action(SHUFFLE_BUTTON_ACTION_ID)
async def handle_shuffle_click(
    ack: AsyncAck, 
    client: AsyncWebClient, 
    body: Dict[str, Any],
) -> None:
    try:
        # Acknowledge the action
        await ack()
        view_id = body['container']['view_id']
        shuffle_chain = ShuffleChain(
            llm=get_llm(
                **PERSONALITY_MODEL_SETTINGS
            ),
        )
        private_metadata_str = body['view']['private_metadata']
        private_metadata = json.loads(body['view']['private_metadata'])
        old_response = format_slack_to_openai(private_metadata['response'])
        conversation_style = private_metadata['conversation_style']
        slack_user_id = body['user']['id']
        response = await shuffle_chain.async_run(
            old_response=old_response,
            conversation_style=conversation_style,
            slack_user_id=slack_user_id,
        )
        processed_response = format_openai_to_slack(response)
        private_metadata['rephrased_response'] = processed_response
        private_metadata_str = json.dumps(private_metadata)
        response_view = get_view(
            "response_command_modal", 
            private_metadata_str=private_metadata_str, 
            is_using_default_conversation_style=private_metadata['is_using_default_conversation_style'],
            is_rephrasing_stage=True,
            is_rephrase_answer_available=True,
            search_docs=[],
        )
        await client.views_update(view_id=view_id, view=response_view)
    except Exception as e:
        logger.error(f"Error in shuffle click: {e}")
        error_view = get_view("text_command_modal", text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)
        

@slack_app.action(EDIT_BUTTON_ACTION_ID)
async def handle_edit_response(
    ack: AsyncAck, 
    client: AsyncWebClient, 
    logger: Logger,
    body: Dict[str, Any]
) -> None:
    await ack()
    try:
        view_id = body['container']['view_id']
        metadata_dict = json.loads(body['view']['private_metadata'])
        private_metadata = body['view']['private_metadata']        
        response_view = get_view(
            "response_command_modal", 
            private_metadata_str=body['view']['private_metadata'], 
            is_using_default_conversation_style=metadata_dict['is_using_default_conversation_style'],
            is_rephrasing_stage=True,
            is_rephrase_answer_available=True,
            is_edit_view=True,
            search_docs=[],
        )
        await client.views_update(view_id=view_id, view=response_view)
    except Exception as e:
        logger.error(f"Error in edit response: {e}")
        error_view = get_view("text_command_modal", text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)


@slack_app.action(SELECTION_BUTTON_ACTION_ID)
async def handle_selection_button(
    ack: AsyncAck, 
    body: Dict[str, Any],
    client: AsyncWebClient,
) -> None:
    await ack()
    slack_user_id = body['user']['id']
    selected_question = body['actions'][0]['value']
    view_id = body['container']['view_id']
    
    private_metadata = body['view']['private_metadata']
    metadata_dict = json.loads(private_metadata)
    channel_id = metadata_dict['channel_id']
    conversation_style = metadata_dict['conversation_style']
    qdrant_collection_name = metadata_dict['qdrant_collection_name']
    typesense_collection_name = metadata_dict['typesense_collection_name']
    is_using_default_conversation_style = metadata_dict['is_using_default_conversation_style']
    slack_chat_pairs = metadata_dict['slack_chat_pairs']

    await qa_and_response(
        slack_user_id=slack_user_id,
        query=selected_question,
        channel_id=channel_id,
        conversation_style=conversation_style,
        view_id=view_id,
        qdrant_collection_name=qdrant_collection_name,
        typesense_collection_name=typesense_collection_name,
        client=client,
        is_using_default_conversation_style=is_using_default_conversation_style,
        slack_chat_pairs=slack_chat_pairs,
    )