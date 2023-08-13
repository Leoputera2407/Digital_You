from typing import List, Sequence
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from digital_twin.auth.invitation import generate_invitation_token, send_user_invitation_email
from digital_twin.auth.users import current_admin_for_org, current_user
from digital_twin.db.async_slack_bot import async_get_associated_slack_user
from digital_twin.db.engine import get_async_session_generator, get_session
from digital_twin.db.model import (
    Invitation,
    InvitationStatus,
    Organization,
    User,
    UserOrganizationAssociation,
    UserRole,
)
from digital_twin.db.user import (
    async_get_invitation_by_user_and_org,
    async_get_organization_admin_info,
    async_get_user_by_email,
    async_get_user_org_assocations,
    async_get_user_org_by_user_and_org_id,
    get_organization_by_id,
    get_user_by_email,
    get_user_org_by_user_and_org_id,
    is_user_in_organization,
)
from digital_twin.indexdb.qdrant.indexing import create_qdrant_collection
from digital_twin.indexdb.typesense.store import create_typesense_collection
from digital_twin.server.model import (
    OrganizationAdminInfo,
    OrganizationAssociationBase,
    OrganizationCreateRequest,
    OrganizationData,
    OrganizationUpdateInfoRequest,
    SlackUserDataResponse,
    StatusResponse,
    UserByEmail,
    UserOrgResponse,
)
from digital_twin.utils.collection_key import get_unique_collection_keys
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/organization")


################
# User Account #
################


@router.get("/get-user-org-and-roles", response_model=UserOrgResponse)
async def get_user_org_and_roles(
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> UserOrgResponse:
    if user is None:
        raise HTTPException(status_code=404, detail="Invalid or missing user.")

    user_org_assocations = await async_get_user_org_assocations(user, db_session)
    if not user_org_assocations:
        raise HTTPException(status_code=404, detail="User not found in any organization.")

    user_org = [
        OrganizationAssociationBase(
            id=user_org_assoc.organization.id,
            name=user_org_assoc.organization.name,
            role=user_org_assoc.role,
            joined_at=user_org_assoc.joined_at,
        )
        for user_org_assoc in user_org_assocations
    ]
    return UserOrgResponse(organizations=user_org)


@router.get("/whitelisted-orgs", response_model=StatusResponse[List[OrganizationData]])
async def get_whitelisted_org(
    current_user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[List[OrganizationData]]:
    # Extract the domain from the current user's email
    domain = current_user.email.split("@")[-1]

    result = await db_session.execute(select(Organization))
    organizations: Sequence[Organization] = result.scalars().unique().all()

    whitelisted_orgs = []

    for organization in organizations:
        if organization.whitelisted_email_domain == domain:
            # If the user is already associated with the organization, skip it
            for user_org in current_user.organizations:
                if user_org.organization_id == organization.id:
                    break
            else:
                whitelisted_orgs.append(
                    OrganizationData(
                        id=organization.id,
                        name=organization.name,
                    )
                )

    return StatusResponse(
        success=True,
        message=f"User is whitelisted on the following organizations: {', '.join([org.name for org in whitelisted_orgs])}",
        data=whitelisted_orgs,
    )


@router.get("/verify-org-exists-by-domain", response_model=StatusResponse[OrganizationData])
async def verify_org_exists_by_email_domain(
    current_user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[OrganizationData]:
    user_email = current_user.email
    domain = user_email.split("@")[-1]
    result = await db_session.execute(
        select(Organization).where(Organization.whitelisted_email_domain == domain)
    )
    organization = result.scalars().first()
    if not organization:
        return StatusResponse(success=False, message="No organization found with that email domain.")

    organization_data = OrganizationData(
        name=organization.name,
        id=organization.id,
    )

    return StatusResponse(
        success=True,
        message="Organization found.",
        data=organization_data,
    )


@router.get("/{organization_id}/verify-user-in-org", response_model=StatusResponse)
async def verify_if_user_in_org(
    organization_id: UUID,
    current_user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    result = await db_session.execute(
        select(UserOrganizationAssociation).where(
            UserOrganizationAssociation.user_id == current_user.id,
            UserOrganizationAssociation.organization_id == organization_id,
        )
    )
    association = result.scalars().first()

    # If the association exists, the user is in the organization.
    if association is not None:
        return StatusResponse(success=True, message="User is in the organization.")

    # If the association does not exist, the user is not in the organization.
    else:
        return StatusResponse(
            success=False,
            message=f"User is not in the organization with id {organization_id}.",
        )


@router.post("/create-org-and-add-admin", response_model=StatusResponse)
async def create_organization_and_add_admin(
    org_data: OrganizationCreateRequest,
    current_user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    # First, get the domain from the current user's email
    email_domain = current_user.email.split("@")[-1]
    typesense_collection_key, qdrant_collection_key = get_unique_collection_keys()
    # Then, create a new organization
    new_org = Organization(
        id=str(uuid4()),
        name=org_data.name,
        whitelisted_email_domain=email_domain,
        typesense_collection_key=typesense_collection_key,
        qdrant_collection_key=qdrant_collection_key,
    )

    # Next, create the typesense and qdrant collections
    try:
        create_qdrant_collection(collection_name=qdrant_collection_key)
        create_typesense_collection(collection_name=typesense_collection_key)
    except Exception as e:
        logger.error(f"Error creating collection: {e} for organization: {new_org.id}")
        return StatusResponse(success=False, message="Internal error. Please contact Prosona")

    # Next, add the current user as an admin of the new organization
    user_org_association = UserOrganizationAssociation(
        user_id=current_user.id,
        organization_id=new_org.id,
        role=UserRole.ADMIN,  # assuming 'ADMIN' is a valid role in your UserRole enumeration
    )

    db_session.add(new_org)
    db_session.add(user_org_association)

    # Create an invitation for each user in org_data.users
    for user_email in org_data.invited_users:
        # get the domain from the user's email
        user_domain = user_email.user_email.split("@")[-1]

        # check if the user's email domain matches the whitelisted domain
        if user_domain != email_domain:
            await db_session.rollback()
            return StatusResponse(
                success=False,
                message="User's email domain does not match the organization's whitelisted domain.",
            )

        # if it matches, create an invitation for the user
        invitation_token = generate_invitation_token()
        invite = Invitation(
            organization_id=new_org.id,
            inviter_id=current_user.id,
            invitee_email=user_email.user_email,
            token=invitation_token,
            status=InvitationStatus.PENDING,
        )

        # You might want to catch errors here in case email fails to send
        try:
            send_user_invitation_email(
                workspace_name=new_org.name if new_org.name else "",
                invitee_email=user_email.user_email,
                token=invitation_token,
            )
        except Exception as e:
            logger.error(
                f"Failed to send invitation email to {user_email.user_email} for organization {new_org.name}: {e}"
            )
            await db_session.rollback()
            raise HTTPException(status_code=500, detail="Failed to send invitation email")

        db_session.add(invite)

    try:
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create organization or add user as admin.",
        ) from e

    return StatusResponse(
        success=True,
        message=f"Organization '{new_org.name}' created successfully. User '{current_user.email}' is now an admin.",
    )


""" TODO: Proper invitation flow to do later
@router.post("/{organization_id}/handle-accept-invitation", response_model=StatusResponse)
async def handle_accept_invitation(
    organization_id: UUID,
    current_user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator)
) -> StatusResponse:
    invitation = await async_get_invitation_by_user_and_org(
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
    await db_session.commit()

    return StatusResponse(
        success=True, 
        message="Invitation accepted. User is now part of the organization."
    )
"""


@router.post("/{organization_id}/join-org", response_model=StatusResponse)
async def user_join_org(
    organization_id: UUID,
    current_user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    user_org_association = UserOrganizationAssociation(
        user_id=current_user.id, organization_id=organization_id, role=UserRole.BASIC
    )

    invitation = await async_get_invitation_by_user_and_org(db_session, current_user.email, organization_id)
    # If inviation exists, change the status of the invitation to ACCEPTED
    if invitation:
        invitation.status = InvitationStatus.ACCEPTED
        db_session.add(invitation)

    # Add the new association to the session and commit
    db_session.add(user_org_association)
    await db_session.commit()

    return StatusResponse(success=True, message="User is now part of the organization.")


###################
# Admin Account   #
###################
@router.patch("/{organization_id}/admin/promote-user-to-admin", response_model=StatusResponse)
async def promote_admin(
    organization_id: UUID,
    user_email: UserByEmail,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    user_to_promote = await async_get_user_by_email(db_session, user_email.user_email)
    if not user_to_promote:
        raise HTTPException(status_code=404, detail="User not found")
    user_to_promote_org = await async_get_user_org_by_user_and_org_id(
        db_session, user_to_promote.id, organization_id
    )
    if not user_to_promote_org:
        raise HTTPException(status_code=404, detail="User is not part of the organization")
    user_to_promote_org.role = UserRole.ADMIN
    db_session.add(user_to_promote)
    await db_session.commit()
    return StatusResponse(success=True, message="User promoted to admin successfully.")


@router.post("/{organization_id}/admin/add-user-to-organization", response_model=StatusResponse)
async def add_user_to_org(
    organization_id: UUID,
    user_email: UserByEmail,
    admin_user: User = Depends(current_admin_for_org),
    db_session: Session = Depends(get_session),
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
        logger.error(
            f"Failed to send invitation email to {user_email.user_email} for organization {organization.name}: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to send invitation email")

    db_session.add(invite)
    db_session.commit()

    return StatusResponse(success=True, message="Invitation sent successfully.")


@router.post(
    "/{organization_id}/admin/remove-user-from-organization",
    response_model=StatusResponse,
)
def remove_user_from_org(
    organization_id: UUID,
    user_email: UserByEmail,
    _: User = Depends(current_admin_for_org),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    user_to_remove = get_user_by_email(db_session, user_email.user_email)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")

    user_to_remove_org = get_user_org_by_user_and_org_id(db_session, user_to_remove.id, organization_id)
    if not user_to_remove_org:
        raise HTTPException(status_code=404, detail="User is not part of the organization")

    db_session.delete(user_to_remove_org)
    db_session.commit()

    return StatusResponse(success=True, message="User removed successfully from the organization.")


@router.delete("/{organization_id}/admin/remove-invitation", response_model=StatusResponse)
async def remove_invitation(
    organization_id: UUID,
    user_email: UserByEmail,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    # Get the invitation using the invitee_email and organization_id
    result = await db_session.execute(
        select(Invitation).where(
            Invitation.invitee_email == user_email.user_email,
            Invitation.organization_id == organization_id,
        )
    )
    invitation = result.scalars().first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    await db_session.delete(invitation)
    await db_session.commit()

    return StatusResponse(success=True, message="Invitation removed successfully.")


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


@router.put("/{organization_id}/admin/info", response_model=StatusResponse)
async def update_admin_organization_info(
    organization_id: UUID,
    update_info: OrganizationUpdateInfoRequest,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    organization = await db_session.get(Organization, organization_id)

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if update_info.name is not None:
        organization.name = update_info.name
    """ TODO: White-list domain shouldn't be allowed to change for now.
    if update_info.whitelisted_email_domain is not None:
        organization.whitelisted_email_domain = update_info.whitelisted_email_domain
    """
    await db_session.commit()

    return StatusResponse(
        success=True,
        message="Organization information successfully updated.",
    )


@router.get("/{organization_id}/get-slack-users")
async def get_associated_slack_users(
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[SlackUserDataResponse]:
    slack_user = await async_get_associated_slack_user(db_session, user.id, organization_id)

    if slack_user is None:
        return StatusResponse(success=False, message="No associated Slack user found.")

    return StatusResponse(
        success=True,
        message="Associated Slack user found.",
        data=SlackUserDataResponse(
            slack_team_name=slack_user.slack_organization_association.team_name,
            slack_user_name=slack_user.slack_display_name,
            slack_user_email=slack_user.slack_user_email,
        ),
    )
