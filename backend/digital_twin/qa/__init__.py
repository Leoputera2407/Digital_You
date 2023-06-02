from digital_twin.llm.interface import get_selected_model_config
from digital_twin.qa.interface import QAModel
from digital_twin.qa.question_answer import QA


def get_default_backend_qa_model(supabase_user_id: str) -> QAModel:
    model_config = get_selected_model_config(supabase_user_id)
    # TODO: Max_token_length will default to model's context length for now!
    return QA(model_config=model_config)
    