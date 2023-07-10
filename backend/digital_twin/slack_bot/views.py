import json
from typing import List

LOADING_TEXT = "Thinking..."
PERSONALITY_TEXT = "Learning how you speak from your chat history...This will only happen once!"
ERROR_TEXT ="Something went wrong. Please try again later."
MODAL_RESPONSE_CALLBACK_ID = "response_modal"
EDIT_BUTTON_ACTION_ID ="edit_response"
SHUFFLE_BUTTON_ACTION_ID ="shuffle_response"
EDIT_BLOCK_ID = "edit_block"

def get_view(view_type: str, **kwargs):
    views = {
        "text_command_modal": create_general_text_command_view,
        "response_command_modal": create_response_command_view,
        "edit_command_modal": create_edit_command_view,
    }

    if view_type not in views:
        raise ValueError(f"Unknown view type: {view_type}")

    return views[view_type](**kwargs)


def create_general_text_command_view(text: str) -> None:
    return {
        "type": "modal",
        "callback_id": "text_modal",
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
        private_metadata_str: str, 
        response: str, 
        is_using_default_conversation_style: bool, 
        is_hide_button: bool, 
        search_docs,
) -> None:
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Your AI-generated response:*\n\n" + response
            }
        }
    ]
    
    if not is_hide_button:
        blocks[0]["accessory"] = {
            "type": "button",
            "text": {"type": "plain_text", "text": ":pencil2: Edit", "emoji": True},
            "action_id": EDIT_BUTTON_ACTION_ID
        }
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

    if is_using_default_conversation_style:
        warning_message = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":warning: We're using the default style, as you didn't have enough chat history."
            }
        }
        blocks.insert(1, warning_message)
    
    top_3_docs = "\n".join([
    f"<{doc.link}|{doc.source_type.capitalize()}>\n{doc.blurb}" if doc.link else '' 
    for doc in search_docs[:3]])    
    
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

    return {
        "type": "modal",
        "callback_id": MODAL_RESPONSE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Prosona"},
        "submit": {"type": "plain_text", "text": "Share", "emoji": True},
        "private_metadata": private_metadata_str,
        "blocks": blocks
    }

def create_edit_command_view(private_metadata: str, response: str):
    metadata_dict = json.loads(private_metadata)
    metadata_dict["source"] = "edit"
    private_metadata = json.dumps(metadata_dict)
    return {
        "type": "modal",
        "callback_id": MODAL_RESPONSE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Edit Response"},
        "submit": {"type": "plain_text", "text": "Share"},
        "private_metadata": private_metadata,
        "blocks": [
            {
                "type": "input",
                "block_id": EDIT_BLOCK_ID,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "response_input",
                    "multiline": True,
                    "initial_value": response
                },
                "label": {
                    "type": "plain_text",
                    "text": "Edit your AI-generated response:",
                }
            }
        ]
    }
