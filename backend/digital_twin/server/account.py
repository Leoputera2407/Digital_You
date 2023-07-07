from uuid import UUID
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.auth.users import current_admin_for_org, current_user
from digital_twin.auth.invitation import (
    generate_invitation_token,
    send_user_invitation_email,
)
from digital_twin.db.model import (
    User,
    UserRole,
    Invitation,
    UserOrganizationAssociation,
    InvitationStatus,
    Organization,
)

from digital_twin.db.user import (
    is_user_in_organization,
    get_user_by_email,
    async_get_user_by_email,
    get_user_org_by_user_and_org_id,
    async_get_user_org_by_user_and_org_id,
    get_organization_by_id,
    get_invitation_by_user_and_org,
    get_user_org_assocations,
    async_get_organization_admin_info,
)
from digital_twin.db.engine import (
    get_session,
    get_async_session_generator,
)

from digital_twin.server.model import (
    UserByEmail,
    StatusResponse,
    OrganizationBase,
    UserOrgResponse,
    OrganizationAdminInfo,
    OrganizationName,
    OrganizationUpdateInfoRequest,
)
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/organization")


################
# User Account #
################

@router.get("/get-user-org-and-roles", response_model=UserOrgResponse)
async def get_user_org_and_roles(
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> UserOrgResponse:
    if user is None:
        raise HTTPException(status_code=404, detail="Invalid or missing user.")
    
    user_org_assocations = get_user_org_assocations(user, db_session)
    if not user_org_assocations:
        raise HTTPException(status_code=404, detail="User not found in any organization.")
    
    user_org = [
        OrganizationBase(
            id=user_org_assoc.organization.id,
            name=user_org_assoc.organization.name,
            role=user_org_assoc.role,
            joined_at=user_org_assoc.joined_at,
        )
        for user_org_assoc in user_org_assocations
    ]
    return UserOrgResponse(organizations=user_org)

@router.post("/autojoin-if-whitelisted", response_model=StatusResponse[List[OrganizationName]])
async def autojoin_if_whitelisted(
    current_user: User = Depends(current_user),
    db_session: Session = Depends(get_session)
) -> StatusResponse[List[OrganizationName]]:
    # Extract the domain from the current user's email
    domain = current_user.email.split('@')[-1]

    result = db_session.execute(select(Organization))
    organizations = result.scalars().all()

    joined_orgs = []

    for organization in organizations:
        if organization.whitelisted_email_domain == domain:
            # If the user is already associated with the organization, skip it
            for user_org in current_user.organizations:
                if user_org.organization_id == organization.id:
                    break
            else:
                user_org_association = UserOrganizationAssociation(
                    user_id=current_user.id,
                    organization_id=organization.id,
                    role=UserRole.BASIC
                )
                db_session.add(user_org_association)
                db_session.commit()
                
                joined_orgs.append(OrganizationName(name=organization.name))

    return StatusResponse(
        success=True, 
        message=f"User auto-joined to the following organizations: {', '.join([org.name for org in joined_orgs])}",
        data=joined_orgs
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
    
    # Change the status of the invitation to ACCEPTED
    invitation.status = InvitationStatus.ACCEPTED
    user_org_association = UserOrganizationAssociation(
        user_id=current_user.id,
        organization_id=organization_id,
        role=UserRole.BASIC 
    )

    # Add the new association to the session and commit
    db_session.add(user_org_association)
    db_session.add(invitation)
    db_session.commit()


    return StatusResponse(
        success=True, 
        message="Invitation accepted. User is now part of the organization."
    )



###################
# Admin Account   #
###################
@router.patch("/{organization_id}/admin/promote-user-to-admin", response_model=StatusResponse)
async def promote_admin(
    organization_id: UUID,
    user_email: UserByEmail, 
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator)
) -> StatusResponse:
    user_to_promote = await async_get_user_by_email(
        db_session, 
        user_email.user_email
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
    admin_user: User = Depends(current_admin_for_org),
    db_session: Session = Depends(get_session)
) -> StatusResponse:
    if is_user_in_organization(db_session, user_email.user_email, organization_id):
        raise HTTPException(status_code=404, detail="User is already in the organization")
    
    organization = get_organization_by_id(db_session, organization_id)

    invitation_token = generate_invitation_token()
    invite = Invitation(
        organization_id=organization_id,
        inviter_id=admin_user.id,
        invitee_email=user_email.user_email,
        token=invitation_token,
        status=InvitationStatus.PENDING,
    )
    try:
        send_user_invitation_email(
            workspace_name=organization.name,
            invitee_email=user_email.user_email,
            token=invitation_token,
        )
    except Exception as e:
        logger.error(f"Failed to send invitation email to {user_email.user_email} for organization {organization.name}: {e}")
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
    _: User = Depends(current_admin_for_org),
    db_session: Session = Depends(get_session)
) -> StatusResponse:
    user_to_remove = get_user_by_email(db_session, user_email.user_email)
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

@router.delete("/{organization_id}/admin/remove-invitation", response_model=StatusResponse)
async def remove_invitation(
    organization_id: UUID,
    user_email: UserByEmail, 
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator)
) -> StatusResponse:

    # Get the invitation using the invitee_email and organization_id
    result = await db_session.execute(
        select(Invitation).where(
            Invitation.invitee_email == user_email.user_email,
            Invitation.organization_id == organization_id
        )
    )
    invitation = result.scalars().first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    await db_session.delete(invitation)
    await db_session.commit()

    return StatusResponse(
        success=True,
        message="Invitation removed successfully."
    )


@router.get("/{organization_id}/admin/info", response_model=OrganizationAdminInfo)
async def get_admin_organization_info(
    organization_id: UUID, 
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> OrganizationAdminInfo: 
    organization_info = await async_get_organization_admin_info(organization_id, db_session)
    
    if not organization_info:
        raise HTTPException(status_code=404, detail="Organization not found")

    return organization_info


@router.put("/{organization_id}/admin/info", response_model=StatusResponse[OrganizationAdminInfo])
async def update_admin_organization_info(
    organization_id: UUID, 
    update_info: OrganizationUpdateInfoRequest,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[OrganizationAdminInfo]:
    organization = await db_session.get(Organization, organization_id)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if update_info.name is not None:
        organization.name = update_info.name
    if update_info.whitelisted_email_domain is not None:
        organization.whitelisted_email_domain = update_info.whitelisted_email_domain
    
    db_session.commit()

    return StatusResponse(
        success=True,
        message="Organization information successfully updated.",
    )