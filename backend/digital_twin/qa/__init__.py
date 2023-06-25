from typing import Optional
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.qa.interface import QAModel
from digital_twin.qa.question_answer import QA

from digital_twin.db.model import User


def get_default_backend_qa_model(
    model_timeout: int = 10, 
) -> QAModel:
    return QA(
        model_timeout=model_timeout,
    )


async def async_get_default_backend_qa_model(
    model_timeout: int = 10,
) -> QAModel:
    return QA(
        model_timeout=model_timeout,
    )