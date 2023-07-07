import {
    addUserToOrganization,
    promoteUserToAdmin,
    removeUserFromOrganization,
    updateAdminOrganizationInfo,
} from "@/lib/adminUser";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { OrganizationAdminInfo, OrganizationUpdateInfo } from "@/lib/types";
import { useState } from "react";
import useSWR, { mutate } from "swr";

interface UseOrgAdminOpsReturn {
  isLoading: boolean;
  adminOrgInfo: OrganizationAdminInfo | undefined;
  isAdminOrgInfoError: boolean;
  revalidateAdminOrgInfo: () => void;
  handleAddUserToOrg: (userEmail: string) => Promise<void>;
  handleRemoveUserFromOrg: (userEmail: string, isPending: boolean) => Promise<void>;
  handlePromoteUserToAdmin: (userEmail: string) => Promise<void>;
  handleUpdateAdminOrganizationInfo: (
    organizationName: string,
    whitelistedEmailDomain: string
  ) => Promise<void>;
}

export function useOrgAdminOps(
  organizationId: string | undefined | null
): UseOrgAdminOpsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const { data, error } = useSWR<OrganizationAdminInfo>(
    organizationId ? `/api/organization/${organizationId}/admin/info` : null,
    (url) => fetcher(url, axiosInstance)
  );

  const handleAddUserToOrg = async (userEmail: string) => {
    setIsLoading(true);
    // Optimistic Update
    mutate(
      `/api/organization/${organizationId}/admin/info`,
      (currentData: OrganizationAdminInfo | undefined) => {
        if (!currentData) return undefined;
        // Create a new invitation entry, assuming the addition is successful
        const newPendingInvitation = { email: userEmail, status: "pending" };
        return {
          ...currentData,
          pending_invitations: [
            ...currentData.pending_invitations,
            newPendingInvitation,
          ],
        };
      },
      false // Do not re-fetch immediately
    );

    try {
      const validOrganizationId = verifyOrganizationId(organizationId);

      await addUserToOrganization(
        axiosInstance,
        validOrganizationId,
        userEmail
      );
      publish({
        variant: "success",
        text: "Successfully added user to organization!",
      });
      // After server update, re-fetch to ensure data is up-to-date
      mutate(`/api/organization/${organizationId}/admin/info`);
    } catch (error: any) {
      // Rollback to server state on error
      mutate(`/api/organization/${organizationId}/admin/info`);
      publish({
        variant: "danger",
        text: "Failed to add user to organization!",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveUserFromOrg = async (
    userEmail: string,
    isPending: boolean
  ) => {
    setIsLoading(true);
    // Optimistic update
    mutate(
      `/api/organization/${organizationId}/admin/info`,
      (currentData: OrganizationAdminInfo | undefined) => {
        if (!currentData) return undefined;
        if (isPending) {
          return {
            ...currentData,
            pending_invitations: currentData.pending_invitations.filter(
              (invitation) => invitation.email !== userEmail
            ),
          };
        } else {
          return {
            ...currentData,
            users: currentData.users.filter(
              (user) => user.user_email !== userEmail
            ),
          };
        }
      },
      false // Do not re-fetch immediately
    );

    try {
      const validOrganizationId = verifyOrganizationId(organizationId);

      await removeUserFromOrganization(
        axiosInstance,
        validOrganizationId,
        userEmail
      );
      publish({
        variant: "success",
        text: "Successfully removed user from organization!",
      });
      // After server update, re-fetch to ensure data is up-to-date
      mutate(`/api/organization/${organizationId}/admin/info`);
    } catch (error: any) {
      // Rollback to server state on error
      mutate(`/api/organization/${organizationId}/admin/info`);
      publish({
        variant: "danger",
        text: "Failed to remove user from organization!",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromoteUserToAdmin = async (userEmail: string) => {
    setIsLoading(true);
    // We shouldn't optimisiically update here,
    // since we don't know if the user is already an admin
    try {
      const validOrganizationId = verifyOrganizationId(organizationId);

      await promoteUserToAdmin(axiosInstance, validOrganizationId, userEmail);
      publish({
        variant: "success",
        text: "Successfully promoted user to admin!",
      });
      mutate(`/api/organization/${organizationId}/admin/info`);
    } catch (error: any) {
      publish({
        variant: "danger",
        text: "Failed to promote user to admin!",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateAdminOrganizationInfo = async (
    organizationName: string,
    whitelistedEmailDomain: string
  ) => {
    setIsLoading(true);
    // Optimistic update
    mutate(
      `/api/organization/${organizationId}/admin/info`,
      (currentData: OrganizationAdminInfo | undefined) => {
        if (!currentData) return undefined;

        return {
          ...currentData,
          name: organizationName,
          whitelisted_email_domain: whitelistedEmailDomain,
        };
      },
      false // Do not re-fetch immediately
    );

    try {
      const validOrganizationId = verifyOrganizationId(organizationId);
      const updateInfo: OrganizationUpdateInfo = {
        name: organizationName,
        whitelisted_email_domain: whitelistedEmailDomain,
      };

      await updateAdminOrganizationInfo(
        axiosInstance,
        validOrganizationId,
        updateInfo
      );

      publish({
        variant: "success",
        text: "Successfully updated organization information!",
      });
      // After server update, re-fetch to ensure data is up-to-date
      mutate(`/api/organization/${organizationId}/admin/info`);
    } catch (error: any) {
      // Rollback to server state on error
      mutate(`/api/organization/${organizationId}/admin/info`);

      publish({
        variant: "danger",
        text: "Failed to update organization information!",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    adminOrgInfo: data,
    isAdminOrgInfoError: error,
    revalidateAdminOrgInfo: () =>
      mutate(`/api/organization/${organizationId}/admin/info`),
    handleAddUserToOrg,
    handleRemoveUserFromOrg,
    handlePromoteUserToAdmin,
    handleUpdateAdminOrganizationInfo,
  };
}

function verifyOrganizationId(organizationId?: string | null): string {
  if (organizationId === undefined || organizationId === null) {
    throw new Error("Organization ID is undefined");
  }
  return organizationId;
}
