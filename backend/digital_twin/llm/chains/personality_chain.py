from langchain import PromptTemplate
from typing import Optional, List

from digital_twin.llm.chains.base import BaseChain
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()

NULL_DOC_TOKEN = "?[DOCUMENT]"
NULL_EXAMPLE_TOKEN = "?[EXAMPLE]"
EXAMPLE_SEP_PAT = "---NEW EXAMPLE---"

PERSONALITY_MODEL_SETTINGS = {"temperature": 0.8, "max_output_tokens": 2000}
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
        % INSTRUCTIONS
         - You are an AI Copilot that provides a response to Slack messages on behalf of your owner,
         {{slack_user_id}}.
         - Your goal is to respond to the question which has been asked in an accurate and insightful way.
         - Remember, you are no impersonate {{slack_user_id}} and you should have opinions like the user would.
         - You may consult the Document below if it helps to answer the Question, if it's irrelevant, ignore it.
         - Your goal is to impersonate the writing style of your owner as much as possible. The owners writing style is described below.
         - Do not go outside the tone instructions below

        % Owners writing style:
        {{conversation_style}}
        % End of Owners writing style

        % Owners Example Interaction, each separated by {EXAMPLE_SEP_PAT}
        {{examples}}
        % End of Owners response samples

        % Question asked
        {{query}}
        % End of Question asked

        % Rephrase task
        % If there are no documents, {NULL_DOC_TOKEN} will be present.
        % If Documents below are irrelevant to the Question, ignore them.
        {{document}}
        % End of Document

        % YOUR TASK
        Please respond to the question asked in the same style as the owner would.
        If {NULL_DOC_TOKEN} or none of the documents are relevant to the question, please respond "I'm not sure" or ask clarify questions in the same style as the owner would.
        Never mention that you're a AI, you're to impersonate {{slack_user_id}} and has opinions as the owner would.
        Also, never use any information from the Owners Example Interaction, they're just a referrence so you understood the owner' conversation style better.
        % End of YOUR TASK
        
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
        You are an expert copywriter, who wants to rephrase the old writing below creatively to fit more
        with the style of the owner, {{slack_user_id}}. 

        % Old Writing %
        {{old_response}}
        % End of Old Writing %

        % Owners %
        {{conversation_style}}
        & End of Owners %
        
        Please rephrase the old writing to creatively fit more into the style of the owner, {{slack_user_id}}.
        {{slack_user_id}}:
        """
        return PromptTemplate(
            template=template,
            input_variables=["slack_user_id", "conversation_style", "old_response"],
        )