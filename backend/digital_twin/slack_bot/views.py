import json

LOADING_TEXT = "Thinking..."
PERSONALITY_TEXT = "Learning how you speak from your chat history...This will only happen once!"
ERROR_TEXT ="Something went wrong. Please try again later."

def get_view(view_type, **kwargs):
    views = {
        "text_command_modal": create_general_text_command_view,
        "response_command_modal": create_response_command_view,
        "shuffle_command_modal": create_shuffle_command_view,
        "edit_command_modal": create_edit_command_view,
    }

    if view_type not in views:
        raise ValueError(f"Unknown view type: {view_type}")

    return views[view_type](**kwargs)


def create_general_text_command_view(text):
    return {
        "type": "modal",
        "callback_id": "response_modal",
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
        "callback_id": "command_modal",
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
                    "action_id": "edit_response"
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":twisted_rightwards_arrows: Shuffle", "emoji": True},
                        "action_id": "shuffle_response"
                    }
                ]
            }
        ]
    }

def create_shuffle_command_view():
    return {
        "type": "modal",
        "callback_id": "response_modal",
        "title": {"type": "plain_text", "text": "Digital Twin"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Thinking..."
                }
            }
        ]
    }

def create_edit_command_view(private_metadata, response):
    return {
        "type": "modal",
        "callback_id": "edit_response_modal",
        "title": {"type": "plain_text", "text": "Edit Response"},
        "submit": {"type": "plain_text", "text": "Update"},
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



def open_command_modal(client, trigger_id):
    loading_view = {
        "type": "modal",
        "callback_id": "response_modal",
        "title": {"type": "plain_text", "text": "Digital Twin"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Thinking..."
                }
            }
        ]
    }
    response = client.views_open(trigger_id=trigger_id, view=loading_view)
    return response["view"]["id"]


def update_command_modal_response(client, channel_id, view_id, response, query):
    private_metadata_str = json.dumps(
        {"response": response, "channel_id": channel_id, "query": query})
    actual_view = {
        "type": "modal",
        "callback_id": "command_modal",
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
                    "action_id": "edit_response"
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": ":twisted_rightwards_arrows: Shuffle", "emoji": True},
                        "action_id": "shuffle_response"
                    }
                ]
            }
        ]
    }
    client.views_update(view_id=view_id, view=actual_view)


def update_command_modal_text(client, view_id, text):
    loading_view = {
        "type": "modal",
        "callback_id": "response_modal",
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
    client.views_update(view_id=view_id, view=loading_view)

