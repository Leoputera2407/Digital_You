class DatabaseError(Exception):
    """Base class for exceptions in this module."""

    pass


class SlackUserAlreadyExistsError(DatabaseError):
    def __init__(self, slack_team_name, slack_user_email):
        self.slack_team_name = slack_team_name
        self.slack_user_email = slack_user_email
        self.error_message = (
            f"Slack user with email {slack_user_email} is already integrated for {slack_team_name} workspace."
        )


class SlackOrgNotFoundError(DatabaseError):
    def __init__(self, slack_team_name):
        self.slack_team_name = slack_team_name
        self.error_message = f"{slack_team_name} workspace is not supported. Please contact your admin."
