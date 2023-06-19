from typing import cast, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from digital_twin.server.model import (
    APIKeyBase, 
    BaseModelConfig, 
    StatusResponse,
    ObjectCreationIdResponse,
)
from digital_twin.db.model import DB_MODEL_PLATFORM, DBAPIKeyType

from digital_twin.db.llm import (
    upsert_api_key,
    get_db_api_key,
    delete_api_key,
    upsert_model_config,
    get_model_config_by_user,
    mask_api_key,
)
from digital_twin.utils.api_key import check_api_key_is_valid
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.auth_bearer import JWTBearer

logger = setup_logger()
#router = APIRouter(prefix="/model", dependencies=[Depends(JWTBearer())])
router = APIRouter(prefix="/model")

@router.post("/api-key/validate")
def validate_model_api_key(
    request: APIKeyBase,
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


@router.get("/api-key/{user_id}", response_model=List[APIKeyBase])
def get_model_api_key(
    user_id: str,
    key_type: Optional[DBAPIKeyType] = Query(None),
) -> List[APIKeyBase]:
    try:
        api_keys = get_db_api_key(user_id, key_type.value if key_type else None)
        # only get last 4 characters of key to not expose full key

        return [
            APIKeyBase(
                key_type=api_key.key_type,
                key_value=mask_api_key(cast(str, api_key.key_value))
            ) for api_key in api_keys
        ]
    except Exception:
        raise HTTPException(status_code=404, detail="Key not found")


@router.post("/api-key/{user_id}",  response_model=ObjectCreationIdResponse)
def store_model_api_key(
    user_id: str,
    request: APIKeyBase,
) -> ObjectCreationIdResponse:
    try:
        api_key_db = APIKeyBase(**request.dict())
        api_key_inserted = upsert_api_key(user_id, api_key_db)
        if not api_key_inserted:
            raise HTTPException(400, "Failed to store API key")
        return api_key_inserted
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@router.delete("/api-key/{user_id}")
def delete_model_api_key(
    user_id: str,
    key_type: DBAPIKeyType = Query(...),
) -> StatusResponse:
    if not delete_api_key(user_id, key_type.value):
        raise HTTPException(404, "API Key not found")
    return StatusResponse(success=True, message="API Key deleted successfully")
    

@router.post("/model-config/{user_id}", response_model=ObjectCreationIdResponse)
def upsert_model_config_endpoint(
    user_id: str,
    model_config: BaseModelConfig
) -> ObjectCreationIdResponse:
    model_config_db = BaseModelConfig(**model_config.dict())
    model_config = upsert_model_config(user_id, model_config_db)
    if model_config is None:
        raise HTTPException(status_code=400, detail="Model Config not found")
    return model_config

@router.get("/model-config/{user_id}", response_model=BaseModelConfig)
def get_model_config_by_user_endpoint(
    user_id: str
) -> BaseModelConfig:
    result = get_model_config_by_user(user_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Model Config not found")
    return BaseModelConfig(**result.dict())