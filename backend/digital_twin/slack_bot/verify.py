from digital_twin.config.app_config import NUM_DOCS
from digital_twin.verify import get_default_backend_verify_model
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def verify_chain(supabase_user_id, slack_user_id, query, docs):
    verify_response: str = None
    if docs:
        verify_model = get_default_backend_verify_model(supabase_user_id)
        try:
            verify_response = verify_model.answer_question(
                query, docs[:NUM_DOCS]
            )
        except Exception as e:
            logger.error(f"Error answering question for {slack_user_id}: {e}")
            raise Exception(f"Error answering question for {slack_user_id}: {e}")
           
    return verify_response