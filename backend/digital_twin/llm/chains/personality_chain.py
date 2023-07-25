from langchain import PromptTemplate
from typing import Optional, List

from digital_twin.llm.chains.base import BaseChain
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()

NULL_DOC_TOKEN = "?[DOCUMENT]"
NULL_EXAMPLE_TOKEN = "?[EXAMPLE]"
EXAMPLE_SEP_PAT = "---NEW EXAMPLE---"

PERSONALITY_MODEL_SETTINGS = {"temperature": 0.3, "max_output_tokens": 2000}
class BasePersonalityChain(BaseChain):
    """
    Base class for Personality.
    """
    def format_examples(self, examples: Optional[List[str]] = None) -> str:
        """Format the examples for the prompt."""
        if examples is None:
            return ""
        return "".join(
            f"{EXAMPLE_SEP_PAT}\n{example}\n"
            for example in examples
        ).strip()
    
    def get_filled_prompt(self, examples: Optional[List[str]] = None, **kwargs) -> str:
        if examples is None:
           formatted_prompt = self.create_prompt(**kwargs) 
        elif examples == []:
            kwargs["examples"] = NULL_EXAMPLE_TOKEN
            formatted_prompt = self.create_prompt(**kwargs)
        else:
            # Create a copy to avoid altering the original list
            examples = list(examples)     
            # Keep adding more examples until we hit the token limit
            for idx, _ in enumerate(examples):
                kwargs["examples"] = self.format_examples(examples[:idx+1])
                formatted_prompt = self.create_prompt(**kwargs)
                if not self.tokens_within_limit(formatted_prompt):
                    examples.pop(idx)
                    break
            logger.debug(f"Stuffed {len(examples)} examples in the context")
        return formatted_prompt
    
    @log_function_time()
    def run(self, examples: Optional[List[str]] = None, **kwargs) -> str:
        formatted_prompt = self.get_filled_prompt(examples, **kwargs)
        return self.llm.predict(formatted_prompt)
    
    @log_function_time()
    async def async_run(self, examples: Optional[List[str]] = None, **kwargs) -> str:
        formatted_prompt = self.get_filled_prompt(examples, **kwargs)
        return await self.llm.apredict(formatted_prompt)


class PersonalityChain(BasePersonalityChain):
    """
    Custom class for generating a verbose list of tone attributes and a verbose description to describe a set of answers.
    """

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        prompt = (
            "Generate a verbose list of tone attributes and a verbose description "
            "to describe the conversation style for user {slack_user_id} from "
            "example interaction given below."
            "Things like pace, mood, etc.\n\n"
            f'Each sample interaction below is prefixed with "{EXAMPLE_SEP_PAT}".\n\n'
            "{examples}\n\n---\n\n"
            "Respond with nothing else besides the sample interactions."
            "Give a verbose list describing the user in the format below\n"
            "% Start Format %\n"
            "Tone attributes:\n"
            "Conversation style:\n"
            "% End Format %"
        )
        return PromptTemplate(
            template=prompt, input_variables=["examples", "slack_user_id"]
        )


class RephraseChain(BasePersonalityChain):
    """
    Custom class for generating a response to a Slack message on behalf of a user.
    """

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        template = f"""
        % INSTRUCTIONS \n
         - You are an expert copywriter that provides a response to workplace Slack messages on behalf of your owner,
         {{slack_user_id}}. \n
         - Your goal is to respond to the question which has been asked in an accurate, authentic and insightful way. \n
         - Remember, you are to impersonate {{slack_user_id}} and you should have the perspective and opinions like the user would. \n
         - You may consult the Document below if it helps to answer the Question, if it's irrelevant, ignore it. \n
         - Your goal is to match the conversation style of your owner as much as possible. The owners conversation style is described below. \n
         - If there is no conversation style recorded, then use a style that is suitable for workplace communication. Make sure to sound like and authentic human. \n
         - NEVER refer to yourself or {{slack_user_id}} directly. \n
         - Do not go outside the tone instructions below \n\n

        % Owners conversation style:\n
        {{conversation_style}}
        % End of Owners conversation style\n\n

        % Owners Example Interaction, each separated by {EXAMPLE_SEP_PAT}\n
        {{examples}}
        % End of Owners response samples\n\n

        % Question asked\n
        {{query}}
        % End of Question asked\n\n

        % Rephrase task\n
        % If there are no documents, {NULL_DOC_TOKEN} will be present.
        % If Documents below are irrelevant to the Question, ignore them.\n
        % DOCUMENT START\n
        {{document}}
        % DOCUMENT END \n\n

        % YOUR TASK\n
        Please respond to the question asked in the same style as the owner would.
        If {NULL_DOC_TOKEN} or none of the documents are relevant to the question, please respond "I'm not sure" or ask clarify questions in the same style as the owner would.
        Never mention that you're a AI, you're to impersonate {{slack_user_id}} and has opinions as the owner would.
        Also, never use any information from the Owners Example Interaction, they're just a reference so you understood the owner' conversation style better.
        % End of YOUR TASK\n\n
        
        {{slack_user_id}}:
        """
        return PromptTemplate(
            template=template,
            input_variables=["examples", "conversation_style", "query", "slack_user_id", "document"],
        )

class ShuffleChain(BasePersonalityChain):
    """
    Custom class for generating a response to a Slack message on behalf of a user.
    """

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        template = f"""
        % INSTRUCTIONS
         - You are an expert copywriter that provides a response to workplace Slack messages on behalf of your owner,
         - Rephrase the initial draft 
         - Remember, you are to impersonate {{slack_user_id}} and you should have the perspective and opinions like the user would. \n
         - NEVER refer to yourself or {{slack_user_id}} directly. \n
         
        with the style of the owner, {{slack_user_id}}. 

        % initial draft %
        {{old_response}}
        % End of initial draft %

        % Owners Conversation style %
        {{conversation_style}}
        & End of Owners %
        
        Please rephrase the initial draft while maintaining {{slack_user_id}} conversation style.
        
        If there is no conversation style recorded, then use a style that is suitable for workplace communication. Make sure to sound like and authentic human.
        """
        return PromptTemplate(
            template=template,
            input_variables=["slack_user_id", "conversation_style", "old_response"],
        )