import asyncio
import json
from typing import Any, List, Optional

from slack_bolt import BoltResponse
from slack_bolt.async_app import AsyncAck, AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import MIN_CHAT_PAIRS_THRESHOLD, WEB_DOMAIN
from digital_twin.db.async_slack_bot import async_get_chat_pairs
from digital_twin.db.engine import get_async_session
from digital_twin.db.model import SlackUser
from digital_twin.db.user import (
    async_get_organization_id_from_team_id,
    async_get_qdrant_collection_for_slack,
    async_get_slack_user_by_email,
    async_get_typesense_collection_for_slack,
)
from digital_twin.indexdb.qdrant.store import QdrantVectorDB
from digital_twin.indexdb.typesense.store import TypesenseIndex
from digital_twin.qa import async_get_default_backend_qa_model
from digital_twin.search.interface import async_retrieve_hybrid_reranked_documents
from digital_twin.search.utils import chunks_to_search_docs
from digital_twin.slack_bot.personality import async_handle_user_conversation_style, async_rephrase_response
from digital_twin.slack_bot.utils import retrieve_sorted_past_messages, view_update_with_appropriate_token
from digital_twin.slack_bot.views import (
    ERROR_TEXT,
    LOADING_TEXT,
    create_general_text_command_view,
    create_response_command_view,
    create_selection_command_view,
)
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.slack import format_openai_to_slack, get_slack_channel_type, use_appropriate_token
from digital_twin.utils.timing import log_function_time

logger = setup_logger()


async def qa_and_response(
    query: str,
    channel_id: str,
    channel_type: str,
    team_id: str,
    view_id: str,
    client: AsyncWebClient,
    slack_user_id: str,
    slack_user_token: str,
    view_slack_token: str,
    thread_ts: Optional[str],
    ts: Optional[str],
) -> None:
    """
    This function synthesizes an AI generated response based on the query provided.

    Parameters:
    query (str): The query to generate response.
    channel_id (str): The channel id where the command is triggered.
    team_id (str): The team id where the command is triggered.
    view_id (str): The id of the view to update.
    client (AsyncWebClient): The async Slack client to be used.
    ranked_chunks (List[Document], optional): List of documents ranked by relevance to the query.
    thread_ts (str, optional): The thread timestamp of the message to be updated.
    ts (str, optional): The timestamp of the message to be updated.

    Returns:
    None: This function doesn't return anything but updates the view with the AI generated response.
    """
    async with get_async_session() as session1, get_async_session() as session2, get_async_session() as session3, get_async_session() as session4:
        preprocess_tasks = {
            "conversation_style": async_handle_user_conversation_style(
                session1, client, slack_user_token, slack_user_id, view_slack_token, team_id, view_id
            ),
            "qdrant_collection_name": async_get_qdrant_collection_for_slack(session2, slack_user_id, team_id),
            "typesense_collection_name": async_get_typesense_collection_for_slack(
                session3, slack_user_id, team_id
            ),
        }
        results = await asyncio.gather(*preprocess_tasks.values(), return_exceptions=True)
        for task_name, result in zip(preprocess_tasks.keys(), results):
            if isinstance(result, Exception):
                raise Exception(f"Error in {task_name} coroutine: {result}")
        (
            conversation_style,
            qdrant_collection_name,
            typesense_collection_name,
        ) = results

        slack_chat_pairs = await async_get_chat_pairs(session4, slack_user_id, team_id)

    is_using_default_conversation_style = False
    if len(slack_chat_pairs) < MIN_CHAT_PAIRS_THRESHOLD:
        is_using_default_conversation_style = True
    ranked_chunks, _ = await async_retrieve_hybrid_reranked_documents(
        query=query,
        user_id=None,  # This mean it'll retrieve all public docs (which only that now)
        filters=None,
        vectordb=QdrantVectorDB(collection=qdrant_collection_name),
        keywordb=TypesenseIndex(collection=typesense_collection_name),
    )

    search_docs = chunks_to_search_docs(ranked_chunks)
    if len(search_docs) == 0:
        private_metadata_str = json.dumps(
            {"response": "Cannot find any relevant documents. Please ask a different question!"}
        )
        display_doc_view = create_response_command_view(
            private_metadata_str=private_metadata_str,
            is_using_default_conversation_style=is_using_default_conversation_style,
            is_rephrasing_stage=False,
            search_docs=search_docs,
        )
        await view_update_with_appropriate_token(
            client=client, view=display_doc_view, view_id=view_id, view_slack_token=view_slack_token
        )
        return

    private_metadata_str = json.dumps({"response": "Synthezing AI generated response..."})
    display_doc_view = create_response_command_view(
        private_metadata_str=private_metadata_str,
        is_using_default_conversation_style=is_using_default_conversation_style,
        is_rephrasing_stage=False,
        search_docs=search_docs,
    )
    await view_update_with_appropriate_token(
        client=client, view=display_doc_view, view_id=view_id, view_slack_token=view_slack_token
    )

    qa_model = await async_get_default_backend_qa_model(model_timeout=10)
    (
        qa_response,
        sources,
        is_docs_revelant,
        confidence_score,
    ) = await qa_model.async_answer_question_and_verify(
        query,
        context_docs=ranked_chunks if ranked_chunks else [],
    )

    processed_response = format_openai_to_slack(qa_response if qa_response else "")
    private_metadata_str = json.dumps(
        {
            "response": processed_response,
            "channel_id": channel_id,
            "channel_type": channel_type,
            "slack_user_token": slack_user_token,
            "view_slack_token": view_slack_token,
            "conversation_style": conversation_style,
            "is_docs_revelant": is_docs_revelant,
            "confidence_score": confidence_score,
        }
    )
    response_view = create_response_command_view(
        private_metadata_str=private_metadata_str,
        is_using_default_conversation_style=is_using_default_conversation_style,
        is_rephrasing_stage=True,
        is_rephrase_answer_available=False,
        search_docs=search_docs,
    )
    await view_update_with_appropriate_token(
        client=client, view=response_view, view_id=view_id, view_slack_token=view_slack_token
    )

    rephrased_response = await async_rephrase_response(
        conversation_style=conversation_style,
        query=query,
        slack_user_id=slack_user_id,
        qa_response=qa_response if qa_response else "",
        chat_pairs=slack_chat_pairs,
    )
    private_metadata_str = json.dumps(
        {
            "response": processed_response,
            "rephrased_response": rephrased_response,
            "channel_id": channel_id,
            "channel_type": channel_type,
            "slack_user_token": slack_user_token,
            "view_slack_token": view_slack_token,
            "conversation_style": conversation_style,
            "is_docs_revelant": is_docs_revelant,
            "confidence_score": confidence_score,
            "is_using_default_conversation_style": is_using_default_conversation_style,
            "ts": thread_ts if thread_ts else ts,
        }
    )
    response_view = create_response_command_view(
        private_metadata_str=private_metadata_str,
        is_using_default_conversation_style=is_using_default_conversation_style,
        is_rephrasing_stage=True,
        is_rephrase_answer_available=True,
        search_docs=search_docs,
    )
    await view_update_with_appropriate_token(
        client=client, view=response_view, view_id=view_id, view_slack_token=view_slack_token
    )
    return


@log_function_time()
async def handle_prosona_command(
    ack: AsyncAck,
    command: dict[str, Any],
    payload: dict[str, Any],
    client: AsyncWebClient,
) -> None:
    await ack()
    slack_user_id = command["user_id"]
    slack_team_id = command["team_id"]
    channel_id = command["channel_id"]
    trigger_id = payload["trigger_id"]
    view_slack_token = client.token
    loading_view = create_general_text_command_view(text=LOADING_TEXT)
    response = await client.views_open(trigger_id=trigger_id, view=loading_view)
    view_id = response["view"]["id"]
    try:
        async with get_async_session() as async_db_session:
            # Look up user in our db using their Slack user ID
            organization_id = await async_get_organization_id_from_team_id(
                session=async_db_session,
                team_id=slack_team_id,
            )
            if not organization_id:
                no_org_text = "Prosona is not enabled for this workspace. Please contact your administrator."
                no_org_view = create_general_text_command_view(text=no_org_text)
                await view_update_with_appropriate_token(
                    client=client, view=no_org_view, view_id=view_id, view_slack_token=view_slack_token
                )
                return BoltResponse(status=200)

            slack_user_info = await client.users_info(user=slack_user_id)
            slack_user_email = slack_user_info.get("user", {}).get("profile", {}).get("email", None)
            if not slack_user_email:
                raise ValueError(f"Cannot find email for slack user")
            slack_user: SlackUser = await async_get_slack_user_by_email(async_db_session, slack_user_email)
            if slack_user is None:
                normalized_domain = WEB_DOMAIN.rstrip("/")
                no_associated_user_text = f"You're almost there! Please sign in <{normalized_domain}|here> and integrate to Slack to start using Prosona"
                # body=f"<@{slack_user_id}> You're almost there! Please sign in <{normalized_domain} | here> and integrate to Slack to start using Prosona",
                no_associated_user_view = create_general_text_command_view(text=no_associated_user_text)
                await view_update_with_appropriate_token(
                    client=client,
                    view=no_associated_user_view,
                    view_id=view_id,
                    view_slack_token=view_slack_token,
                )
                return BoltResponse(status=200)

            channel_type = await get_slack_channel_type(
                client=client,
                payload=payload,
                slack_user_token=slack_user.slack_user_token,
            )
            use_appropriate_token(
                client=client,
                channel_type_str=channel_type.value,
                slack_user_token=slack_user.slack_user_token,
            )
        # Get the latest message from the channel
        past_messages = await retrieve_sorted_past_messages(
            client=client,
            channel_id=channel_id,
            channel_type=channel_type.value,
            limit_scanned_messages=5,
        )
        if not past_messages:
            error_view = create_general_text_command_view(
                text="Cannot find any messages in the channel. Please try again later!"
            )
            await view_update_with_appropriate_token(
                client=client, view=error_view, view_id=view_id, view_slack_token=view_slack_token
            )
            return

        # NOTE: Due to the async interaction of slack actions, i.e. button clicks,
        # we need to handle the qa in the slack action handler.
        # Please refer to the `handle_selection_button` for the continuation of the qa

        # We need to parcel all the necessary metadata into the private_metadata field
        # Remember there's a 3000 word limit.
        private_metadata_str = json.dumps(
            {
                "channel_id": channel_id,
                "channel_type": channel_type.value,
                "slack_user_token": slack_user.slack_user_token,
                "view_slack_token": view_slack_token,
            }
        )
        # Create the selection modal view and open it
        selection_view = create_selection_command_view(
            past_messages=past_messages,
            private_metadata_str=private_metadata_str,
            in_thread=False,
        )
        await view_update_with_appropriate_token(
            client=client, view=selection_view, view_id=view_id, view_slack_token=view_slack_token
        )
        return
    except Exception as e:
        logger.info(f"Error handling Prosona for {slack_user_id}: {e}")
        error_view = create_general_text_command_view(text=ERROR_TEXT)
        await view_update_with_appropriate_token(
            client=client, view=error_view, view_id=view_id, view_slack_token=view_slack_token
        )
        return
