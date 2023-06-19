from digital_twin.llm.interface import get_selected_model_config
from digital_twin.verify.interface import VerifyModel
from digital_twin.qa.question_answer import QA


def get_default_backend_verify_model(supabase_user_id: str) -> VerifyModel:
    model_config = get_selected_model_config(supabase_user_id)
    # TODO: Max_token_length will default to model's context length for now!
    return VerifyModel(model_config=model_config)
    