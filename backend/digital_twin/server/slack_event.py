import json
from collections.abc import Awaitable, Callable
from logging import Logger
from typing import Any, Dict
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from slack_bolt import BoltResponse
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncAck, AsyncApp, AsyncBoltContext
from slack_bolt.error import BoltError
from slack_bolt.oauth.async_oauth_flow import AsyncOAuthFlow
from slack_bolt.request.payload_utils import is_action, is_event, is_view
from slack_sdk.http_retry.builtin_async_handlers import AsyncRateLimitErrorRetryHandler
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from starlette.responses import Response as StarletteResponse

from digital_twin.auth.users import current_user
from digital_twin.config.app_config import WEB_DOMAIN
from digital_twin.db.engine import get_async_session_generator
from digital_twin.db.model import SlackIntegration, User, UserRole
from digital_twin.db.user import async_get_user_org_by_user_and_org_id
from digital_twin.llm.chains.personality_chain import PERSONALITY_MODEL_SETTINGS, ShuffleChain
from digital_twin.llm.interface import get_llm
from digital_twin.server.model import AuthUrl
from digital_twin.slack_bot.config import get_oauth_settings
from digital_twin.slack_bot.events.command import handle_prosona_command, qa_and_response
from digital_twin.slack_bot.events.home_tab import build_home_tab
from digital_twin.slack_bot.utils import retrieve_sorted_past_messages
from digital_twin.slack_bot.views import (
    EDIT_BLOCK_ID,
    EDIT_BUTTON_ACTION_ID,
    ERROR_TEXT,
    LOADING_TEXT,
    MODAL_RESPONSE_CALLBACK_ID,
    SELECTION_BUTTON_ACTION_ID,
    SHUFFLE_BUTTON_ACTION_ID,
    create_general_text_command_view,
    create_response_command_view,
    create_selection_command_view,
)
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.slack import (
    SlackResponseStatus,
    custom_handle_installation,
    custom_handle_slack_oauth_redirect,
    format_openai_to_slack,
    format_slack_to_openai,
    to_starlette_response,
    use_appropriate_token,
)

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
        )
        or (
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
    # slack_app.event("app_mention")(ack=just_ack, lazy=[respond_to_app_mention])
    # slack_app.event("message")(ack=just_ack, lazy=[respond_to_new_message])
    slack_app.command("/prosona")(ack=just_ack, lazy=[handle_prosona_command])
    slack_app.command("/staging-prosona")(ack=just_ack, lazy=[handle_prosona_command])
    # slack_app.action(SHUFFLE_BUTTON_ACTION_ID)(ack=just_ack, lazy=[])
    # slack_app.view(MODAL_RESPONSE_CALLBACK_ID)(lazy=[])


register_listeners(slack_app)

app_handler = AsyncSlackRequestHandler(slack_app)


@router.post("/slack/events")
async def handle_slack_event(req: Request):
    return await app_handler.handle(req)


@router.get("/slack/install/{organization_id}")
async def install(
    response: StarletteResponse,
    organization_id: UUID,
    request: Request,
    slack_integration_type: SlackIntegration = Query(...),
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> AuthUrl:
    oauth_flow: AsyncOAuthFlow = app_handler.app.oauth_flow
    user_association = await async_get_user_org_by_user_and_org_id(db_session, user.id, organization_id)
    if slack_integration_type == SlackIntegration.CONNECTOR.value and user_association.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Access denied. User is not an admin for this organization.",
        )

    if oauth_flow is not None and request.method == "GET":
        bolt_resp = await custom_handle_installation(
            user=user,
            oauth_flow=oauth_flow,
            organization_id=organization_id,
            db_session=db_session,
            request=request,
            slack_integration_type=slack_integration_type,
        )
        # Convert bolt response to starlette response
        res = to_starlette_response(bolt_resp)

        # Extract state from the cookie
        cookie_header = res.headers.get("set-cookie", "")
        if "=" in cookie_header and ";" in cookie_header:
            state = cookie_header.split("=")[1].split(";")[0]
        else:
            logger.error("Invalid or missing 'set-cookie' header in response")
            raise HTTPException(status_code=500, detail="Internal server error")

        # Prepare the auth URL
        auth_url = res.body.decode()

        # Set cookies
        response.set_cookie(
            key="slack-app-oauth-state",
            value=state,
            samesite="None",
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
    if (
        oauth_flow is not None
        and request.url.path == oauth_flow.redirect_uri_path
        and request.method == "GET"
    ):
        res = await custom_handle_slack_oauth_redirect(
            oauth_flow=oauth_flow,
            db_session=db_session,
            request=request,
        )
        if isinstance(res, SlackResponseStatus):
            base_redirect_url = res.redirect_url
            # If status code indicates success, redirect to the settings page
            if res.success:
                return RedirectResponse(url=base_redirect_url)
            else:  # On failure, redirect to the WEB_DOMAIN with the status and body as query parameters
                error_data = {
                    "status": res.status_code,
                    "error_message": res.error_message,
                    "connector_type": "slack",
                }
                return RedirectResponse(url=f"{base_redirect_url}?{urlencode(error_data)}")

        raise HTTPException(
            status_code=500,
            detail="Unexpected response type from custom_handle_slack_oauth_redirect",
        )
    return StarletteResponse(
        status_code=404,
        content="Not found",
    )


@slack_app.event("url_verification")
async def handle_url_verification(body: Dict[str, Any]):
    challenge = body.get("challenge")
    return {"challenge": challenge}


@slack_app.event("app_home_opened")
async def render_home_tab(client: AsyncWebClient, context: AsyncBoltContext) -> None:
    db_user_id = context.get("DB_USER_ID", None)
    if not db_user_id:
        slack_user_id = context.get("user_id", "")
        team_id = context.get("team_id", "")
        if not slack_user_id or not team_id:
            # Wierd edge-case, just in case we get a bad payload
            raise BoltError(f"Error while verifying the slack token")
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

    payload: Dict[str, Any] = json.loads(body["view"]["private_metadata"])
    channel_id = payload["channel_id"]
    thread_ts = payload["ts"]
    slack_user_token = payload["slack_user_token"]
    channel_type = payload["channel_type"]
    slack_user_token = payload["slack_user_token"]
    use_appropriate_token(
        client=client,
        channel_type_str=channel_type,
        slack_user_token=slack_user_token,
    )

    # Check if the submission is from the edit view
    if payload.get("source") == "edit":
        # Here, instead of using the original response from payload,
        # get the updated response from the user's input
        response = body["view"]["state"]["values"][EDIT_BLOCK_ID]["response_input"]["value"]
    else:
        response = payload["rephrased_response"]

    await client.chat_postMessage(
        channel=channel_id,
        text=response,
        username=body["user"]["username"],
        token=slack_user_token,
        thread_ts=thread_ts,
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
        view_id = body["container"]["view_id"]
        shuffle_chain = ShuffleChain(
            llm=get_llm(
                temperature=PERSONALITY_MODEL_SETTINGS["temperature"],
                max_output_tokens=int(PERSONALITY_MODEL_SETTINGS["max_output_tokens"]),
            )
        )
        slack_user_id = body["user"]["id"]
        private_metadata_str = body["view"]["private_metadata"]
        private_metadata = json.loads(body["view"]["private_metadata"])
        old_response = format_slack_to_openai(private_metadata["rephrased_response"])
        conversation_style = private_metadata["conversation_style"]
        channel_type = private_metadata["channel_type"]
        slack_user_token = private_metadata["slack_user_token"]
        use_appropriate_token(
            client=client,
            channel_type_str=channel_type,
            slack_user_token=slack_user_token,
        )

        response = await shuffle_chain.async_run(
            old_response=old_response,
            conversation_style=conversation_style,
            slack_user_id=slack_user_id,
        )
        processed_response = format_openai_to_slack(response)
        private_metadata["rephrased_response"] = processed_response
        private_metadata_str = json.dumps(private_metadata)
        response_view = create_response_command_view(
            private_metadata_str=private_metadata_str,
            is_using_default_conversation_style=private_metadata["is_using_default_conversation_style"],
            is_rephrasing_stage=True,
            is_rephrase_answer_available=True,
            search_docs=[],
        )
        await client.views_update(view_id=view_id, view=response_view)
    except Exception as e:
        logger.error(f"Error in shuffle click: {e}")
        error_view = create_general_text_command_view(text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)


@slack_app.action(EDIT_BUTTON_ACTION_ID)
async def handle_edit_response(
    ack: AsyncAck, client: AsyncWebClient, logger: Logger, body: Dict[str, Any]
) -> None:
    await ack()
    try:
        view_id = body["container"]["view_id"]
        private_metadata = body["view"]["private_metadata"]
        metadata_dict = json.loads(private_metadata)
        channel_type = metadata_dict["channel_type"]
        slack_user_token = metadata_dict["slack_user_token"]
        use_appropriate_token(
            client=client,
            channel_type_str=channel_type,
            slack_user_token=slack_user_token,
        )
        response_view = create_response_command_view(
            private_metadata_str=private_metadata,
            is_using_default_conversation_style=metadata_dict["is_using_default_conversation_style"],
            is_rephrasing_stage=True,
            is_rephrase_answer_available=True,
            is_edit_view=True,
            search_docs=[],
        )
        await client.views_update(view_id=view_id, view=response_view)
    except Exception as e:
        logger.error(f"Error in edit response: {e}")
        error_view = create_general_text_command_view(text=ERROR_TEXT)
        await client.views_update(view_id=view_id, view=error_view)


@slack_app.action(SELECTION_BUTTON_ACTION_ID)
async def handle_selection_button(
    ack: AsyncAck,
    body: Dict[str, Any],
    client: AsyncWebClient,
    context: AsyncBoltContext,
) -> None:
    await ack()
    view_id = body["container"]["view_id"]
    loading_view = create_general_text_command_view(text=LOADING_TEXT)
    await client.views_update(view_id=view_id, view=loading_view)

    slack_user_id = body["user"]["id"]
    team_id = body["team"]["id"]
    button_value = json.loads(body["actions"][0]["value"])
    selected_question = button_value["message"]
    thread_ts = button_value["thread_ts"]
    ts = button_value["ts"]
    in_thread = button_value["in_thread"]

    private_metadata = body["view"]["private_metadata"]
    metadata_dict = json.loads(private_metadata)
    channel_id = metadata_dict["channel_id"]
    channel_type = metadata_dict["channel_type"]
    slack_user_token = metadata_dict["slack_user_token"]
    use_appropriate_token(
        client=client,
        channel_type_str=channel_type,
        slack_user_token=slack_user_token,
    )

    if thread_ts is None or in_thread:
        # This means user have selected to
        # (1) answer a standalone message
        # (2) answer a message in a thread
        await qa_and_response(
            slack_user_id=slack_user_id,
            slack_user_token=slack_user_token,
            query=selected_question,
            channel_id=channel_id,
            team_id=team_id,
            view_id=view_id,
            client=client,
            context=context,
            thread_ts=thread_ts,
            ts=ts,
        )
    else:
        # Get the latest message from the thread
        past_messages = await retrieve_sorted_past_messages(
            client,
            channel_id,
            channel_type=channel_type,
            thread_ts=thread_ts,
            limit_scanned_messages=50,
        )
        parent_message = past_messages[0]
        remaining_messages = past_messages[1:]
        latest_5_remaining_messages = remaining_messages[-5:]
        messages_to_select = [parent_message] + latest_5_remaining_messages
        selection_view = create_selection_command_view(
            past_messages=messages_to_select,
            private_metadata_str=private_metadata,
            in_thread=True,
        )
        await client.views_update(view_id=view_id, view=selection_view)
        return
