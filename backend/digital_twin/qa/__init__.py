from typing import Optional
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.llm.interface import get_selected_model_config, async_get_selected_model_config
from digital_twin.qa.interface import QAModel
from digital_twin.qa.question_answer import QA

from digital_twin.db.model import User


def get_default_backend_qa_model(
        db_session: Session,
        max_output_token: int = 500,   # about 300 words
        user: Optional[User] = None, 
) -> QAModel:
    model_config = get_selected_model_config(user, db_session)
    return QA(
        db_session=db_session,
        model_config=model_config,
        max_output_tokens=max_output_token,
        user=user,
    )


async def async_get_default_backend_qa_model(
        db_session: AsyncSession,
        max_output_token: int = 500,   # about 300 words
        user: Optional[User] = None, 
) -> QAModel:
    model_config = await async_get_selected_model_config(user, db_session)
    return QA(
        db_session=db_session,
        model_config=model_config, 
        max_output_tokens=max_output_token,
        user=user,
    )