import openai
from openai.error import AuthenticationError, Timeout

def check_api_key_is_valid(api_key: str, key_type: str) -> bool:
    if not api_key:
        return False

    # For now only check openai, if antrophic is always true for now.
    if key_type.startswith("openai"):
        # try for up to 2 timeouts (e.g. 4 seconds in total)
        for _ in range(3):
            try:
                openai.Completion.create(
                    api_key=api_key,
                    model="gpt-3.5-turbo",
                    prompt="Don't response",
                )
                return True
            except AuthenticationError:
                return False
            except Timeout:
                pass
    elif key_type.startswith("anthrophic"):
        # TODO: handle antrophic model
        return True
    else:
        raise ValueError(f"Unknown key type: {key_type}")

    return False