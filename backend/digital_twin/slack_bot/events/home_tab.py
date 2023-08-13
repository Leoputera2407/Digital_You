def build_home_tab(message: str) -> dict:
    return {
        "type": "home",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
                "accessory": {
                    "action_id": "configure",
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Configure"},
                    "style": "primary",
                    "value": "api_key",
                },
            }
        ],
    }
