from digital_twin.config.app_config import NUM_DOCS
from digital_twin.qa import get_default_backend_qa_model
from digital_twin.utils.logging import setup_logger


logger = setup_logger()


def handle_qa_response(supabase_user_id, slack_user_id, query, docs):
    qa_response: str = None
    if docs:
        qa_model = get_default_backend_qa_model(supabase_user_id)
        try:
            qa_response = qa_model.answer_question(
                query, docs[:NUM_DOCS]
            )
        except Exception as e:
            logger.error(f"Error answering question for {slack_user_id}: {e}")
            raise Exception(f"Error answering question for {slack_user_id}: {e}")
           
    return qa_response
