import json
from typing import Optional
from postgrest import APIResponse


import json
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from digital_twin.db.model import GoogleAppCredential
from digital_twin.utils.logging import setup_logger, log_sqlalchemy_error


logger = setup_logger()

@log_sqlalchemy_error(logger)
def fetch_db_google_app_creds(db_session: Session) -> Optional[GoogleAppCredential]:
    stmt = select(GoogleAppCredential)
    result = db_session.execute(stmt)
    credential = result.scalars().first()
    return credential

@log_sqlalchemy_error(logger)
def upsert_db_google_app_cred(app_credential: GoogleAppCredential, db_session: Session) -> Optional[GoogleAppCredential]:
    stmt = select(GoogleAppCredential).order_by(GoogleAppCredential.updated_at.desc())
    result = db_session.execute(stmt)
    credentials = result.scalars().all()

    if len(credentials) >= 1:
        # If existing credentials found, update it
        credential = credentials[0]
        credential.credentials_json = json.dumps(app_credential)
        
        # If more than one row, delete all but the most recent
        if len(credentials) > 1:
            for extra_credential in credentials[1:]:
                db_session.delete(extra_credential)
    else:
        # If no credentials found, create new
        credential = GoogleAppCredential(credentials_json=json.dumps(app_credential))
        db_session.add(credential)

    db_session.commit()
    return credential


