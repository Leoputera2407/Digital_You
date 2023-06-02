import json


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

