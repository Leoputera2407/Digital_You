
from typing import cast, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.auth.users import current_admin_user, current_user
from digital_twin.db.model import (
    User,
    UserRole,
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
