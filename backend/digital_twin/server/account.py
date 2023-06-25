
from typing import cast, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.auth.user import current_admin_user, current_user
from digital_twin.server.model import (
    APIKeyBase, 
    BaseModelConfig, 
    StatusResponse,
    ObjectCreationIdResponse,
)
from digital_twin.db.model import (
    DB_MODEL_PLATFORM, 
    DBAPIKeyType,
    User,
    UserRole,
)

from digital_twin.db.llm import (
    upsert_api_key,
    get_db_api_key,
    delete_api_key,
    upsert_model_config,
    get_model_config_by_user,
    mask_api_key,
)
from digital_twin.db.user import (
    async_get_user_by_email
)
from digital_twin.db.engine import (
    get_sqlalchemy_async_engine,
    get_session,
)

from digital_twin.server.model import (
    UserByEmail,
    UserRoleResponse,

)

from digital_twin.utils.api_key import check_api_key_is_valid
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/account")


################
# User Account #
################
@router.get("/get-user-role", response_model=UserRoleResponse)
async def get_user_role(
    user: User = Depends(current_user)
) -> UserRoleResponse:
    if user is None:
        raise ValueError("Invalid or missing user.")
    return UserRoleResponse(role=user.role)



###################
# Admin Account   #
###################

@router.patch("/admin/promote-user-to-admin", response_model=None)
async def promote_admin(
    user_email: UserByEmail, 
    user: User = Depends(current_admin_user)
) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    async with AsyncSession(get_sqlalchemy_async_engine()) as asession:
        user_to_promote = await async_get_user_by_email(asession, user_email)
        if not user_to_promote:
            raise HTTPException(status_code=404, detail="User not found")
        user_to_promote.role = UserRole.ADMIN
        asession.add(user_to_promote)
        await asession.commit()
    return

@router.post("/admin/add-user-to-organization", response_model=None)
async def add_user_to_org(
    user_email: UserByEmail, 
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session)
) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # TODO: Add supabase sign_up_flow to create user by email
    return

@router.post("/admin/remove-user-to-organization", response_model=None)
async def remove_user_from_org(
    user_email: UserByEmail, 
    user: User = Depends(current_admin_user)
) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    async with AsyncSession(get_sqlalchemy_async_engine()) as asession:
        user_to_remove = await async_get_user_by_email(asession, user_email)
        if not user_to_remove:
            raise HTTPException(status_code=404, detail="User not found")
        user_to_remove.role = UserRole.BASIC
        user_to_remove.organization_id = None
        asession.add(user_to_remove)
        await asession.commit()
    return


@router.post("/admin/api-key/validate")
def validate_model_api_key(
    request: APIKeyBase,
    _: User = Depends(current_admin_user),
) -> StatusResponse:
    try:
        if request.key_type in DB_MODEL_PLATFORM:
            is_valid = check_api_key_is_valid(request.key_value, request.key_type.value)
        else:
            is_valid = True
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid API key provided")

    return StatusResponse(success=True, message="API Key is valid")


@router.get("/admin/api-key", response_model=List[APIKeyBase])
def get_model_api_key(
    key_type: Optional[DBAPIKeyType] = None,
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> List[APIKeyBase]:
    try:
        api_keys = get_db_api_key(db_session, user, key_type.value if key_type else None)
        # only get last 4 characters of key to not expose full key
        return [
            APIKeyBase(
                key_type=api_key.key_type,
                key_value=mask_api_key(cast(str, api_key.key_value))
            ) for api_key in api_keys
        ]
    except Exception:
        raise HTTPException(status_code=404, detail="Key not found")


@router.post("/admin/api-key",  response_model=ObjectCreationIdResponse)
def store_model_api_key(
    request: APIKeyBase,
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> ObjectCreationIdResponse:
    try:
        api_key_db = APIKeyBase(**request.dict())
        api_key_inserted = upsert_api_key(user, api_key_db, db_session)
        if not api_key_inserted:
            raise HTTPException(400, "Failed to store API key")
        return api_key_inserted
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@router.delete("/admin/api-key")
def delete_model_api_key(
    key_type: DBAPIKeyType,
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    if not delete_api_key(user, key_type.value, db_session):
        raise HTTPException(404, "API Key not found")
    return StatusResponse(success=True, message="API Key deleted successfully")
    

@router.post("/admin/model-config", response_model=ObjectCreationIdResponse)
def upsert_model_config_endpoint(
    model_config: BaseModelConfig,
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> ObjectCreationIdResponse:
    model_config_db = BaseModelConfig(**model_config.dict())
    model_config = upsert_model_config(user, model_config_db, db_session)
    if model_config is None:
        raise HTTPException(status_code=400, detail="Model Config not found")
    return model_config

@router.get("/admin/model-config", response_model=BaseModelConfig)
def get_model_config_endpoint(
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> BaseModelConfig:
    result = get_model_config_by_user(db_session, user)
    if result is None:
        raise HTTPException(status_code=400, detail="Model Config not found")
    return BaseModelConfig(**result.dict())