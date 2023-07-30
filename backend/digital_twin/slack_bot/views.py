import json
from typing import List

LOADING_TEXT = "Thinking..."
PERSONALITY_TEXT = "Learning how you speak from your chat history...This will only happen once!"
ERROR_TEXT ="Something went wrong. Please try again later."
MODAL_RESPONSE_CALLBACK_ID = "response_modal"
EDIT_BUTTON_ACTION_ID ="edit_response"
SHUFFLE_BUTTON_ACTION_ID ="shuffle_response"
SELECTION_BUTTON_ACTION_ID ="selection_response"
EDIT_BLOCK_ID = "edit_block"

def create_general_text_command_view(text: str) -> None:
    return {
        "type": "modal",
        "callback_id": "text_modal",
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "title": {"type": "plain_text", "text": "Prosona"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": text
                }
            }
        ]
    }

def create_response_command_view(
        is_using_default_conversation_style: bool, 
        is_rephrasing_stage: bool, 
        search_docs,
        private_metadata_str: str = '{}',
        is_rephrase_answer_available: bool = False,
        is_edit_view: bool = False
) -> None:
    metadata_dict = json.loads(private_metadata_str)

    blocks = []

    if is_rephrasing_stage:
        if is_edit_view:
            metadata_dict["source"] = "edit"
            # add the multiline_plain_text input for editing response
            edit_section = {
                "type": "input",
                "block_id": EDIT_BLOCK_ID,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "response_input",
                    "multiline": True,
                    "initial_value": metadata_dict["rephrased_response"]  # set the initial value to rephrase response
                },
                "label": {
                    "type": "plain_text",
                    "text": "Edit your AI-generated response:",
                }
            }
            blocks.append(edit_section)
        else:
            # add the new section for rephrase answer
            rephrase_text = metadata_dict["rephrased_response"] if is_rephrase_answer_available else "Rephrasing to sound like you"
            metadata_dict["source"] = "ai_response"
            rephrase_section = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Rephrased Response:*\n\n" + rephrase_text
                    },
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":pencil2: Edit", "emoji": True},
                        "action_id": EDIT_BUTTON_ACTION_ID
                    }
                }
            blocks.append(rephrase_section)
        
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":twisted_rightwards_arrows: Shuffle", "emoji": True},
                        "action_id": SHUFFLE_BUTTON_ACTION_ID
                    }
                ]
            })
        if is_using_default_conversation_style and is_rephrasing_stage:
            warning_message = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":warning: We're using the default style, as you didn't have enough chat history."
                }
            }
            blocks.append(warning_message)

            

    # add the main response section
    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Your AI-generated response:*\n\n" + metadata_dict["response"]
            }
        }
    )
    confidence_score_label = {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"*Confidence Score:* {metadata_dict.get('confidence_score', 'N/A')}"
            }
        ]
    }
    blocks.append(confidence_score_label)
    if metadata_dict.get("is_docs_relevant", True) is False:
        warning_message = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":warning: Our model is unsure if this answers your question"
            }
        }
        blocks.append(warning_message)   

    if search_docs:
        top_3_docs = "\n".join([
            f"<{doc.link}|{doc.source_type.capitalize()}>\n{doc.blurb}" if doc.link else '' 
            for doc in search_docs[:3]]
        ) 
        blocks.extend([
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Top 3 most relevant documents:*\n\n" + top_3_docs
                }
            }
        ])

    private_metadata_str = json.dumps(metadata_dict)
    return {
        "type": "modal",
        "callback_id": MODAL_RESPONSE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Prosona"},
        "submit": {"type": "plain_text", "text": "Share", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "private_metadata": private_metadata_str,
        "blocks": blocks
    }


def create_selection_command_view(
        past_messages: List[dict[str, any]],
        private_metadata_str: str,
        in_thread: bool = False
) -> dict[str, any]:
    buttons = [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Answer This!" if m['thread_ts'] is None or in_thread else "Go to Thread",
                "emoji": True
            },
            "style": "primary",  # Make the button green
            "value": json.dumps({
                "message": m['message'], 
                "thread_ts": m['thread_ts'],
                "ts": m['ts'],
                "in_thread": in_thread,
            }),  # Store the message and thread_ts as JSON
            "action_id": SELECTION_BUTTON_ACTION_ID 
        }
        for m in past_messages 
    ]
    
    zip_message = zip(buttons, past_messages)

    # Each button is put in a separate section
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{m['sender']}: {json.loads(button['value'])['message']}"  # The question is displayed here
            },
            "accessory": button
        }
        for button, m in zip_message
    ]

    if in_thread:
        blocks.insert(0, {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "You're in a thread!",
                "emoji": True
            }
        })

    # Add the blocks to the view
    view = {
        "type": "modal",
        "callback_id": "selection_modal",
        "title": {"type": "plain_text", "text": "Prosona"},
        "blocks": blocks,
        "private_metadata": private_metadata_str
    }

    return view
