import re 
import time 
from uuid import UUID
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Tuple, Union
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from slack_bolt import BoltResponse
from slack_bolt.async_app import AsyncBoltRequest
from slack_bolt.oauth.async_callback_options import (
    AsyncFailureArgs,
)
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError


from slack_sdk.oauth.installation_store import Installation
from slack_bolt.error import BoltError
from slack_bolt.oauth.async_oauth_flow import AsyncOAuthFlow

from digital_twin.config.app_config import WEB_DOMAIN
from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType
from digital_twin.db.model import User, SlackIntegration
from digital_twin.db.user import (
    async_get_user_by_id,
    async_insert_slack_user,  
    async_upsert_org_to_slack_team  
)
from digital_twin.db.connectors.credentials import (
    async_create_credential,
)
from digital_twin.db.connectors.connectors import (
    async_fetch_connectors,
    async_create_connector,
)
from digital_twin.db.connectors.connector_credential_pair import (
    async_add_credential_to_connector,
)
from digital_twin.db.error import SlackUserAlreadyExistsError, SlackOrgNotFoundError
from digital_twin.server.model import StatusResponse, ConnectorBase, CredentialBase
from digital_twin.utils.logging import setup_logger
logger = setup_logger()


class SlackResponseStatus(BaseModel):
    success: bool
    status_code: int
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None


def to_async_bolt_request(
    req: Request,
    body: bytes,
    addition_context_properties: Optional[Dict[str, Any]] = None,
) -> AsyncBoltRequest:
    request = AsyncBoltRequest(
        body=body.decode("utf-8"),
        query=req.query_params,
        headers=req.headers,
    )
    if addition_context_properties is not None:
        for k, v in addition_context_properties.items():
            request.context[k] = v
    return request


def to_starlette_response(bolt_resp: BoltResponse) -> Response:
    resp = Response(
        status_code=bolt_resp.status,
        content=bolt_resp.body,
        headers=bolt_resp.first_headers_without_set_cookie(),
    )
    for cookie in bolt_resp.cookies():
        for name, c in cookie.items():
            resp.set_cookie(
                key=name,
                value=c.value,
                max_age=c.get("max-age"),
                expires=c.get("expires"),
                path=c.get("path"),
                domain=c.get("domain"),
                secure=True,
                httponly=True,
            )
    return resp

async def custom_handle_installation(
    user: User, 
    oauth_flow: AsyncOAuthFlow,
    organization_id: UUID,
    db_session: AsyncSession,
    request: Request,
    slack_integration_type: SlackIntegration,
) -> BoltResponse:
    bolt_request: AsyncBoltRequest = to_async_bolt_request(
        req=request,
        body=await request.body(),
        addition_context_properties=None,
    )
    set_cookie_value: Optional[str] = None
    url = await oauth_flow.build_authorize_url("", bolt_request)
    if oauth_flow.settings.state_validation_enabled is True:
        state = await oauth_flow.settings.state_store.async_issue(
            prosona_user_id=user.id,
            prosona_org_id=organization_id,
            slack_integration_type=slack_integration_type,
            db_session=db_session,
        )
        url = await oauth_flow.build_authorize_url(state, bolt_request)
        set_cookie_value = oauth_flow.settings.state_utils.build_set_cookie_for_new_state(state)
    
    return BoltResponse(
        status=200,
        body=url,
        headers=await oauth_flow.append_set_cookie_headers(
                {"Content-Type": "text/html; charset=utf-8"},
                set_cookie_value,
            ),
    )

async def associate_slack_user_with_db_user(
        redirect_url: str,
        installation: Installation,
        prosona_org_id: UUID,
        prosona_user: User,
        db_session: AsyncSession
) -> Union[Dict[str, Tuple[User, str]], SlackResponseStatus]:
    admin_slack_user_id = installation.user_id
    admin_slack_team_id = installation.team_id
    slack_token = installation.bot_token
    slack_user_token = installation.user_token
    slack_user_info = await async_get_user_info(admin_slack_user_id, slack_token)
    slack_user_email = slack_user_info.get('profile', {}).get('email', None)
    slack_display_name = slack_user_info.get('real_name')
    if prosona_user is None or slack_user_email is None:
        return SlackResponseStatus(
            success=False,
            status_code=400,
            error_message="slack_user_email_not_found. Please contact admin.",
            redirect_url=redirect_url,
        )

    res = await async_insert_slack_user(
            db_session,
            admin_slack_user_id, 
            admin_slack_team_id,
            db_user_id=prosona_user.id,
            slack_user_token=slack_user_token,
            slack_display_name=slack_display_name,
            slack_user_email=slack_user_email,
            slack_team_name=installation.team_name,
    )

    if isinstance(res, SlackUserAlreadyExistsError) \
        or isinstance(res, SlackOrgNotFoundError):
        return SlackResponseStatus(
            success=False,
            status_code=400,
            error_message=res.error_message,
            redirect_url=redirect_url,
        )

    return {"user": prosona_user, "slack_token": slack_token}

async def handle_credential_and_connector(
        user: User,
        slack_token: str,
        slack_team_name: str,
        prosona_org_id: UUID,
        db_session: AsyncSession,
        oauth_flow: AsyncOAuthFlow,
        request: AsyncBoltRequest
) -> Union[BoltResponse, StatusResponse]:
    # Add credentials for the admin slack user
    cred = CredentialBase(
        credential_json={
            "slack_bot_token": slack_token,
        },
        public_doc=True,
    )

    create_cred_resp = await async_create_credential(
        credential_data=cred,
        user=user,
        organization_id=prosona_org_id,
        db_session=db_session,
    )

    cred_id = create_cred_resp.id

    if cred_id is None:
        return await oauth_flow.failure_handler(
            AsyncFailureArgs(
                request=request,
                reason="insert_credential_failed",
                suggested_status_code=500,
                settings=oauth_flow.settings,
                default=oauth_flow.default_callback_options,
            )
        )
 
    #TODO: Ideally, we should make the connector client side, 
    # since there are parts that we want to make configurable, but 
    # for now, we will do it server-side
    connector_data = ConnectorBase(
        name=f"SlackConnector-{slack_team_name}",
        source=DocumentSource.SLACK,
        input_type=InputType.POLL,
        connector_specific_config={
            "workspace": slack_team_name,
        },
        refresh_freq=60*30,  # Every 30 mins
        public_doc=True,
        disabled=True,
    )
    await async_create_connector(
        connector_data=connector_data,
        organization_id=prosona_org_id,
        db_session=db_session,
    )
    org_slack_connector = await async_fetch_connectors(
        db_session,
        organization_id=prosona_org_id,
        sources=[DocumentSource.SLACK],
    )

    if not org_slack_connector:
        return await oauth_flow.failure_handler(
            AsyncFailureArgs(
                request=request,
                reason="slack_connector_not_found",
                suggested_status_code=500,
                settings=oauth_flow.settings,
                default=oauth_flow.default_callback_options,
            )
        )
    
    link_resp = await async_add_credential_to_connector(
        connector_id=org_slack_connector[0].id,  # Assumes there are only one slackConnector
        credential_id=cred_id,
        db_session=db_session,
        user=user,
        organization_id=prosona_org_id,
    )
    return link_resp


async def custom_handle_slack_oauth_redirect(
    oauth_flow: AsyncOAuthFlow,
    db_session: AsyncSession,
    request: Request,
) -> SlackResponseStatus:
    """
    Handles the installation flow's callback request from Slack.
    This function associate the admin user to slack user using the email address.
    It assumes that email address to sign up to Prosona == email address to sign up to Slack.

    Within this function, we also create credentials for the admin slack user.
    It also assumes that connector is already created for organization.
    """
    # Steps below are copied over from https://github.com/slackapi/bolt-python/blob/3e5f012767d37eaa01fb0ea55bd6ae364ecf320b/slack_bolt/oauth/async_oauth_flow.py#L215
    # Reason why we have to copy is because we have a custom flow to store and associate installer to admin person.
    default_redirect_url = f"{WEB_DOMAIN}/settings"
    bolt_request: AsyncBoltRequest = to_async_bolt_request(
        req=request,
        body=await request.body(),
        addition_context_properties=None,
    )
    # failure due to end-user's cancellation or invalid redirection to slack.com
    error = bolt_request.query.get("error", [None])[0]
    if error is not None:
        return SlackResponseStatus(
            success=False, 
            status_code=400, 
            error_message=f"error: {error}",
            redirect_url=default_redirect_url,
        )

    # state parameter verification
    if oauth_flow.settings.state_validation_enabled is True:
        state: Optional[str] = bolt_request.query.get("state", [None])[0]
        db_state, prosona_org_id, prosona_user_id, slack_integration_type = \
            await oauth_flow.settings.state_store.async_consume(
                state,
                db_session,
            )  # type: ignore
        if slack_integration_type == SlackIntegration.CONNECTOR:
            default_redirect_url = f"{WEB_DOMAIN}/settings/admin/connectors"
        if not db_state or db_state != state:
            return SlackResponseStatus(
                success=False,
                status_code=400,
                error_message="invalid_state",
                redirect_url=default_redirect_url,
            )

    # run installation
    code = bolt_request.query.get("code", [None])[0]
    if code is None:
        return SlackResponseStatus(
            success=False, 
            status_code=400, 
            error_message="invalid_code",
            redirect_url=default_redirect_url,
        )

    installation: Installation = await oauth_flow.run_installation(code)
    if installation is None:
        # failed to run installation with the code
        return SlackResponseStatus(
            success=False, 
            status_code=500,
            error_message="invalid_code",
            redirect_url=default_redirect_url,
        )

    prosona_user = await async_get_user_by_id(
        db_session,
        prosona_user_id,
    )
    if slack_integration_type == SlackIntegration.CONNECTOR:
        # Since only admin org can install connectors,
        # we can upsert the slack team assocation to user's org
        await async_upsert_org_to_slack_team(
            session=db_session,
            team_id=installation.team_id,
            organization_id=prosona_org_id,
            slack_team_name=installation.team_name,
        )
    if slack_integration_type == SlackIntegration.USER:
        # We need to associate slack_user installer 
        # with our DB user, and we do so by looking up the email
        associate_result = await associate_slack_user_with_db_user(
            redirect_url=default_redirect_url,
            installation=installation,
            prosona_user=prosona_user,
            prosona_org_id=prosona_org_id,
            db_session=db_session,
        )
        if isinstance(associate_result, SlackResponseStatus):
            return associate_result

    if slack_integration_type == SlackIntegration.CONNECTOR:
        # Add credentials for the admin slack user
        handle_link_res = await handle_credential_and_connector(
            user=prosona_user,
            slack_token=installation.bot_token,
            slack_team_name=installation.team_name,
            prosona_org_id=prosona_org_id,
            db_session=db_session,
            oauth_flow=oauth_flow,
            request=bolt_request,
        )

        if isinstance(handle_link_res, BoltResponse):
            # if BoltResponse returned, this means an error occurred, so we return it
            return SlackResponseStatus(
                success=False, 
                status_code=500, 
                error_message="link_credential_to_connector_failed",
                redirect_url=default_redirect_url,
            )

        if not handle_link_res.success:                     
            return SlackResponseStatus(
                success=False, 
                status_code=500, 
                error_message="link_credential_to_connector_failed",
                redirect_url=default_redirect_url,
            )

    # persist the installation
    try:
        await oauth_flow.settings.installation_store.async_save(
            installation,
            prosona_org_id = prosona_org_id,
            db_session=db_session,
        )
    except BoltError as err:
        return SlackResponseStatus(
            success=False, 
            status_code=500, 
            error_message="storage_error",
            redirect_url=default_redirect_url,
        )
   
    return SlackResponseStatus(
        success=True, 
        status_code=200,
        redirect_url=default_redirect_url,
    )
  

async def async_get_user_info(slack_user_id: str, slack_token: str) -> dict:
    client = AsyncWebClient(token=slack_token)
    try:
        response = await client.users_info(user=slack_user_id)
        return response["user"]
    except SlackApiError as e:
        logger.error(f"Failed to get user info: {e.response['error']}")


def get_the_last_messages_in_thread(
    sorted_past_messages: List[str],
    time_in_seconds: Optional[int] = 86400, # Last 24 hours
) -> List[str]:
    messages = []
    # Filter old messages by timestamp (in seconds)
    for message in sorted_past_messages:
        seconds = time.time() - float(message.get("ts"))
        if seconds < time_in_seconds:
            messages.append(message)

    return messages

# Conversion from Slack mrkdwn to OpenAI markdown
# See also: https://api.slack.com/reference/surfaces/formatting#basics
def slack_to_markdown(content: str) -> str:
    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for part in parts:
        if part.startswith("```") or part.startswith("`"):
            result += part
        else:
            for o, n in [
                (r"\*(?!\s)([^\*\n]+?)(?<!\s)\*", r"**\1**"),  # *bold* to **bold**
                (r"_(?!\s)([^_\n]+?)(?<!\s)_", r"*\1*"),  # _italic_ to *italic*
                (r"~(?!\s)([^~\n]+?)(?<!\s)~", r"~~\1~~"),  # ~strike~ to ~~strike~~
            ]:
                part = re.sub(o, n, part)
            result += part
    return result


# Conversion from OpenAI markdown to Slack mrkdwn
# See also: https://api.slack.com/reference/surfaces/formatting#basics
def markdown_to_slack(content: str) -> str:
    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for part in parts:
        if part.startswith("```") or part.startswith("`"):
            result += part
        else:
            for o, n in [
                (
                    r"\*\*\*(?!\s)([^\*\n]+?)(?<!\s)\*\*\*",
                    r"_*\1*_",
                ),  # ***bold italic*** to *_bold italic_*
                (
                    r"(?<![\*_])\*(?!\s)([^\*\n]+?)(?<!\s)\*(?![\*_])",
                    r"_\1_",
                ),  # *italic* to _italic_
                (r"\*\*(?!\s)([^\*\n]+?)(?<!\s)\*\*", r"*\1*"),  # **bold** to *bold*
                (r"__(?!\s)([^_\n]+?)(?<!\s)__", r"*\1*"),  # __bold__ to *bold*
                (r"~~(?!\s)([^~\n]+?)(?<!\s)~~", r"~\1~"),  # ~~strike~~ to ~strike~
            ]:
                part = re.sub(o, n, part)
            result += part
    return result


# Format message from Slack to send to OpenAI
def format_slack_to_openai(content: str) -> str:
    if content is None:
        return None

    # Unescape &, < and >, since Slack replaces these with their HTML equivalents
    # See also: https://api.slack.com/reference/surfaces/formatting#escaping
    content = content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    # Convert from Slack mrkdwn to markdown format
    content = slack_to_markdown(content)

    return content

# Format OpenAI to display in Slack
def format_openai_to_slack(content: str) -> str:
    for o, n in [
        # Remove leading newlines
        ("^\n+", ""),
        # Remove prepended Slack user ID
        ("^<@U.*?>\\s?:\\s?", ""),
        # Remove OpenAI syntax tags since Slack doesn't render them in a message
        ("```\\s*[Rr]ust\n", "```\n"),
        ("```\\s*[Rr]uby\n", "```\n"),
        ("```\\s*[Ss]cala\n", "```\n"),
        ("```\\s*[Kk]otlin\n", "```\n"),
        ("```\\s*[Jj]ava\n", "```\n"),
        ("```\\s*[Gg]o\n", "```\n"),
        ("```\\s*[Ss]wift\n", "```\n"),
        ("```\\s*[Oo]objective[Cc]\n", "```\n"),
        ("```\\s*[Cc]\n", "```\n"),
        ("```\\s*[Cc][+][+]\n", "```\n"),
        ("```\\s*[Cc][Pp][Pp]\n", "```\n"),
        ("```\\s*[Cc]sharp\n", "```\n"),
        ("```\\s*[Mm][Aa][Tt][Ll][Aa][Bb]\n", "```\n"),
        ("```\\s*[Jj][Ss][Oo][Nn]\n", "```\n"),
        ("```\\s*[Ll]a[Tt]e[Xx]\n", "```\n"),
        ("```\\s*bash\n", "```\n"),
        ("```\\s*zsh\n", "```\n"),
        ("```\\s*sh\n", "```\n"),
        ("```\\s*[Ss][Qq][Ll]\n", "```\n"),
        ("```\\s*[Pp][Hh][Pp]\n", "```\n"),
        ("```\\s*[Pp][Ee][Rr][Ll]\n", "```\n"),
        ("```\\s*[Jj]ava[Ss]cript\n", "```\n"),
        ("```\\s*[Ty]ype[Ss]cript\n", "```\n"),
        ("```\\s*[Pp]ython\n", "```\n"),
    ]:
        content = re.sub(o, n, content)

    # Convert from OpenAI markdown to Slack mrkdwn format
    content = markdown_to_slack(content)

    return content