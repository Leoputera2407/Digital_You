import { OrganizationUpdateInfo } from "@/lib/types";
import { Axios } from "axios";

export interface StatusResponse {
  success: boolean;
  message: string;
}

export async function promoteUserToAdmin(
  axiosInstance: Axios,
  organizationId: string,
  userEmail: string,
) {
  const response = await axiosInstance.patch(
    `/api/organization/${organizationId}/admin/promote-user-to-admin`,
    { user_email: userEmail}
  );

  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to promote user to admin - ${response.status}`
    );
  }

  return response.data as StatusResponse;
}

export async function addUserToOrganization(
  axiosInstance: Axios,
  organizationId: string,
  userEmail: string,
) {
  const response = await axiosInstance.post(
    `/api/organization/${organizationId}/admin/add-user-to-organization`,
    { user_email: userEmail }
  );

  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to add user to organization - ${response.status}`
    );
  }

  return response.data as StatusResponse;
}

export async function removeUserFromOrganization(
  axiosInstance: Axios,
  organizationId: string,
  userEmail: string,
) {
  const response = await axiosInstance.post(
    `/api/organization/${organizationId}/admin/remove-user-from-organization`,
    { user_email: userEmail }
  );

  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to remove user from organization - ${response.status}`
    );
  }

  return response.data as StatusResponse;
}

export async function removeUserInvitation(
  axiosInstance: Axios,
  organizationId: string,
  userEmail: string,
) {
  const response = await axiosInstance.delete(
    `/api/organization/${organizationId}/admin/remove-invitation`,
    { data: { user_email: userEmail } }
  );

  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to remove user invitation - ${response.status}`
    );
  }

  return response.data as StatusResponse;
}



export async function updateAdminOrganizationInfo(
    axiosInstance: Axios,
    organizationId: string,
    updateInfo: OrganizationUpdateInfo,
  ) {
    const response = await axiosInstance.put(
      `/api/organization/${organizationId}/admin/info`,
      updateInfo
    );
  
    if (response.status < 200 || response.status >= 300) {
      throw new Error(
        `Failed to update organization information - ${response.status}`
      );
    }
  
    return response.data as StatusResponse;
  }