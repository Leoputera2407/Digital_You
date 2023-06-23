from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import NUM_DOCS
from digital_twin.qa import async_get_default_backend_qa_model
from digital_twin.qa.interface import QAModel
from digital_twin.db.model import User
from digital_twin.indexdb.chunking.models import InferenceChunk

from digital_twin.utils.logging import setup_logger

logger = setup_logger()

async def handle_qa_response(
        db_session: AsyncSession,
        user: User, 
        slack_user_id: str, 
        query: str, 
        docs: List[InferenceChunk],
        max_output_token: int = 500,   # about 300 words
) -> Optional[str]:
    qa_response: str = None
    if docs:
        qa_model: QAModel = await async_get_default_backend_qa_model(
            user,
            db_session,
            max_output_token,
        )
        try:
            qa_response = qa_model.async_answer_question(
                query=query, 
                context_docs=docs[:NUM_DOCS]
            )
        except Exception as e:
            logger.error(f"Error answering question for {slack_user_id}: {e}")
            raise Exception(f"Error answering question for {slack_user_id}: {e}")
           
    return qa_response
