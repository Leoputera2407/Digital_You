from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.session import Session

from digital_twin.db.model import User
from digital_twin.qa.interface import QAModel
from digital_twin.qa.question_answer import QA


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
