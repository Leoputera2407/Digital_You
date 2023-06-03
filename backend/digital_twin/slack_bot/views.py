import json

LOADING_TEXT = "Thinking..."
PERSONALITY_TEXT = "Learning how you speak from your chat history...This will only happen once!"
ERROR_TEXT ="Something went wrong. Please try again later."
MODAL_RESPONSE_CALLBACK_ID = "response_modal"
EDIT_BUTTON_ACTION_ID ="edit_response"
SHUFFLE_BUTTON_ACTION_ID ="shuffle_response"

def get_view(view_type, **kwargs):
    views = {
        "text_command_modal": create_general_text_command_view,
        "response_command_modal": create_response_command_view,
        "edit_command_modal": create_edit_command_view,
    }

    if view_type not in views:
        raise ValueError(f"Unknown view type: {view_type}")

    return views[view_type](**kwargs)


def create_general_text_command_view(text):
    return {
        "type": "modal",
        "callback_id": "text_modal",
        "title": {"type": "plain_text", "text": "Digital Twin"},
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

def create_response_command_view(private_metadata_str, response):
    return {
        "type": "modal",
        "callback_id": MODAL_RESPONSE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Digital Twin :gemini:"},
        "submit": {"type": "plain_text", "text": "Share", "emoji": True},
        "private_metadata": private_metadata_str,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Your AI-generated response:*\n\n" + response
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":pencil2: Edit", "emoji": True},
                    "action_id": EDIT_BUTTON_ACTION_ID
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":twisted_rightwards_arrows: Shuffle", "emoji": True},
                        "action_id": SHUFFLE_BUTTON_ACTION_ID
                    }
                ]
            }
        ]
    }

def create_edit_command_view(private_metadata, response):
    return {
        "type": "modal",
        "callback_id": MODAL_RESPONSE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Edit Response"},
        "submit": {"type": "plain_text", "text": "Share"},
        "private_metadata": private_metadata,
        "blocks": [
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "response_input",
                    "initial_value": response
                },
                "label": {
                    "type": "plain_text",
                    "text": "Edit your AI-generated response:",
                }
            }
        ]
    }
