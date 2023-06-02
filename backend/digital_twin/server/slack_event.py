import json

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
from slack_bolt import App, Ack, BoltResponse, BoltContext
from slack_bolt.error import BoltError
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_bolt.request.payload_utils import is_event, is_view, is_action

# TODO: Use this instead
# from digital_twin.llm import get_selected_llm_instance
# from digital_twin.llm.interface import get_selected_model_config
from digital_twin.llm.config import get_api_key
from digital_twin.config.app_config import WEB_DOMAIN
from digital_twin.slack_bot.events.command import handle_digital_twin_command
from digital_twin.slack_bot.events.messages import respond_to_new_message
from digital_twin.slack_bot.events.home_tab import build_home_tab
from digital_twin.slack_bot.config import get_oauth_settings
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.slack import get_slack_supabase_user, insert_slack_supabase_user
from digital_twin.utils.auth_bearer import JWTBearer


logger = setup_logger()
router = APIRouter()


MESSAGE_SUBTYPES_TO_SKIP = ["message_changed", "message_deleted"]
# To reduce unnecessary workload in this app,
# this before_authorize function skips message changed/deleted events.
# Especially, "message_changed" events can be triggered many times when the app rapidly updates its reply.
def before_authorize(
    body: dict,
    payload: dict,
    next_,
):
    if (
        is_event(body)
        and payload.get("type") == "message"
        and payload.get("subtype") in MESSAGE_SUBTYPES_TO_SKIP
    ):
        logger.debug(
            "Skipped the following middleware and listeners "
            f"for this message event (subtype: {payload.get('subtype')})"
        )
        return BoltResponse(status=200, body="")
    
    next_()

slack_app = App(
    oauth_settings=get_oauth_settings(),
    process_before_response=True,
    before_authorize=before_authorize,
    raise_error_for_unhandled_request=True,
)
slack_app.client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))

def just_ack(ack: Ack):
    ack()
def register_listeners(slack_app: App):
    #slack_app.event("app_mention")(ack=just_ack, lazy=[respond_to_app_mention])
    slack_app.event("message")(ack=just_ack, lazy=[respond_to_new_message])
    slack_app.command("/digital-twin")(ack=just_ack, lazy=[handle_digital_twin_command])

register_listeners(slack_app)


app_handler = SlackRequestHandler(slack_app)

class SlackServerSignup(BaseModel):
    supabase_user_id: str
    team_id: str
    slack_user_id: str


@router.get("/slack/server_signup", dependencies=[Depends(JWTBearer())])
async def slack_server_signup(request: Request, signup_info: SlackServerSignup = Depends()):
    try:
        insert_slack_supabase_user(signup_info.slack_user_id, signup_info.team_id, signup_info.supabase_user_id)

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "User successfully signed up."})
    except Exception as e:
        logger.error("Error while signing up slack user: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal Server Error"
        )

@router.post("/slack/events")
async def handle_slack_event(req: Request):
   return await app_handler.handle(req)

from fastapi.responses import RedirectResponse
@router.get("/slack/install")
async def install(req: Request):
    return await app_handler.handle(req)

@router.get("/slack/oauth_redirect")
async def slack_oauth_redirect(request: Request):
    return await app_handler.handle(request)

@slack_app.event("url_verification")
def handle_url_verification(body):
    challenge = body.get("challenge")
    return {"challenge": challenge}

@slack_app.middleware
def set_user_info(client: WebClient, context: BoltContext, payload, body, next_):
    event_type = payload.get('event', {}).get('type', '')
    if event_type == 'app_home_opened':
        next_()
    if is_action(body) or is_view(body):
        slack_user_id = body["user"]["id"]
        team_id = body["team"]["id"]
    else:
        slack_user_id = payload.get("user_id", '')
        team_id = payload.get("team_id", '')
    if not slack_user_id or not team_id:
        # Wierd edge-case, just in case we get a bad payload
        raise BoltError(f'Error while verifying the slack token')
    try:
        # Look up user in external system using their Slack user ID
        supabase_user_id = get_slack_supabase_user(slack_user_id, team_id)
        context["SUPABASE_USER_ID"] = supabase_user_id
    except Exception:
        search_params = f"?slack_user_id={slack_user_id}&team_id={team_id}"
        logger.info(search_params)
        client.chat_postEphemeral(
            channel=payload.get("channel_id", ''),
            user=slack_user_id,
            text=f"Sorry <@{slack_user_id}>, you aren't registered for Digital Twin Service. Please sign up here <{WEB_DOMAIN}/interface/slack{search_params} | Digital Twin Website>"
        )
        raise BoltError(f'Error while verifying the slack token')
    
    # TODO: Use model config, to support other models, for now OPENAI only!
    context["OPENAI_API_KEY"] = get_api_key(
        supabase_user_id,
        "openai_api_key",
    ).key_value
    context["OPENAI_MODEL"] = "gpt-3.5-turbo"
    next_()

@slack_app.event("app_home_opened")
def render_home_tab(client: WebClient, context: BoltContext):
    supabase_user_id = context.get("SUPABASE_USER_ID", None)
    if not supabase_user_id:
        slack_user_id = context.get("user_id", '')
        team_id = context.get("team_id", '')
        if not slack_user_id or not team_id:
            # Wierd edge-case, just in case we get a bad payload
            raise BoltError(f'Error while verifying the slack token')
        search_params = "?slack_user_id={slack_user_id}&team_id={team_id}"
        text = f"""
        To enable this app in this Slack workspace, you need to login to Digital Twin. "
        Visit <{WEB_DOMAIN}/interface/slack{search_params} | Digital Twin Website> to login."
        """
    else:
        text = "Welcome to Digital Twin!"

    client.views_publish(
        user_id=context.user_id,
        view=build_home_tab(text),
    )


@slack_app.view("command_modal")
def handle_view_submission(ack, body, client, logger):
    payload = json.loads(body['view']['private_metadata'])
    response = payload['response']
    channel_id = payload['channel_id']
    client.chat_postMessage(
        channel=channel_id,
        text=response,
        as_user=True,
    )
    logger.info(f"Response sent to channel {channel_id}: {response}")
    ack()

@slack_app.action("shuffle_response")
def handle_shuffle_click(ack, body, client):
    # Acknowledge the action
    ack()
    # Shuffle the response and update the modal here