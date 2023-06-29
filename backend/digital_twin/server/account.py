from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.auth.users import current_admin_user, current_user
from digital_twin.auth.invitation import (
    generate_invitation_token,
    send_user_invitation_email,
)
from digital_twin.db.model import (
    User,
    UserRole,
    Invitation,
    UserOrganizationAssociation,
)

from digital_twin.db.user import (
    is_user_in_organization,
    get_user_by_email,
    async_get_user_by_email,
    get_user_org_by_user_and_org_id,
    async_get_user_org_by_user_and_org_id,
    get_organization_by_id,
    get_invitation_by_user_and_org,
)
from digital_twin.db.engine import (
    get_session,
    get_async_session_generator,
)

from digital_twin.server.model import (
    UserByEmail,
    UserRoleResponse,
    StatusResponse,
)
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/account")


################
# User Account #
################
@router.get("/{organization_id}/get-user-role", response_model=UserRoleResponse)
async def get_user_role(
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session)
) -> UserRoleResponse:
    if user is None:
        raise ValueError("Invalid or missing user.")
    user_org = get_user_org_by_user_and_org_id(
        db_session, 
        user.id, 
        organization_id
    )
    if user_org is None:
        raise HTTPException(status_code=404, detail="User not found in the specified organization")

    return UserRoleResponse(role=user_org.role)


###################
# Admin Account   #
###################

@router.patch("/{organization_id}/admin/promote-user-to-admin", response_model=StatusResponse)
async def promote_admin(
    organization_id: UUID,
    user_email: UserByEmail, 
    user: User = Depends(current_admin_user),
    db_session: AsyncSession = Depends(get_async_session_generator)
) -> StatusResponse:
    admin_user_org = await async_get_user_org_by_user_and_org_id(
        db_session, 
        user.id, 
        organization_id
    )
    if admin_user_org.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_to_promote = await async_get_user_by_email(
        db_session, 
        user_email
    )
    if not user_to_promote:
        raise HTTPException(status_code=404, detail="User not found")
    user_to_promote_org = await async_get_user_org_by_user_and_org_id(
        db_session, 
        user_to_promote.id, 
        organization_id
    )
    if not user_to_promote_org:
        raise HTTPException(status_code=404, detail="User is not part of the organization")
    user_to_promote_org.role = UserRole.ADMIN
    db_session.add(user_to_promote)
    await db_session.commit()
    return StatusResponse(
        success=True,
        message="User promoted to admin successfully."
    )

@router.post("/{organization_id}/admin/add-user-to-organization", response_model=StatusResponse)
async def add_user_to_org(
    organization_id: UUID,
    user_email: UserByEmail, 
    admin_user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_async_session_generator)
) -> StatusResponse:
    user_org = get_user_org_by_user_and_org_id(
        db_session, 
        admin_user.id, 
        organization_id
    )
    if user_org.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if is_user_in_organization(db_session, user_email, organization_id):
        raise HTTPException(status_code=404, detail="User is already in the organization")
    
    organization = get_organization_by_id(db_session, organization_id)

    invitation_token = generate_invitation_token()
    invite = Invitation(
        organization_id=organization_id,
        inviter_id=admin_user.id,
        invitee_email=user_email,
        token=invitation_token,
    )
    try:
        send_user_invitation_email(
            workspace_name=organization.name,
            invitee_email=user_email,
            invitation_token=invitation_token,
        )
    except Exception as e:
        logger.error(f"Failed to send invitation email to {user_email} for organization {organization.name}")
        raise HTTPException(status_code=500, detail="Failed to send invitation email")

    db_session.add(invite)
    db_session.commit()

    return StatusResponse(
        success=True, 
        message="Invitation sent successfully."
    )

@router.post("/{organization_id}/admin/remove-user-from-organization", response_model=StatusResponse)
def remove_user_from_org(
    organization_id: UUID,
    user_email: UserByEmail, 
    admin_user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session)
) -> StatusResponse:
    user_org = get_user_org_by_user_and_org_id(
        db_session, 
        admin_user.id, 
        organization_id
    )
    if user_org.role != UserRole.ADMIN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_to_remove = get_user_by_email(db_session, user_email)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")

    user_to_remove_org = get_user_org_by_user_and_org_id(
        db_session,
        user_to_remove.id,
        organization_id
    )
    if not user_to_remove_org:
        raise HTTPException(status_code=404, detail="User is not part of the organization")

    db_session.delete(user_to_remove_org)
    db_session.commit()

    return StatusResponse(
        success=True, 
        message="User removed successfully from the organization."
    )

@router.get("/{organization_id}/handle-accept-invitation", response_model=StatusResponse)
def handle_accept_invitation(
    organization_id: UUID,
    current_user: User = Depends(current_user),
    db_session: Session = Depends(get_session)
) -> StatusResponse:
    invitation = get_invitation_by_user_and_org(
        db_session, 
        current_user.email, 
        organization_id
    )

    if not invitation:
        return StatusResponse(
            success=False, 
            message="No invitation found."
        )
    
    user_org_association = UserOrganizationAssociation(
        user_id=current_user.id,
        organization_id=organization_id,
        role=UserRole.BASIC 
    )

    # Add the new association to the session and commit
    db_session.add(user_org_association)
    db_session.commit()


    return StatusResponse(
        success=True, 
        message="Invitation accepted. User is now part of the organization."
    )