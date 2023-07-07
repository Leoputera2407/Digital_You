import {
  createConnector,
  deleteConnector,
  linkCredential,
  unlinkCredential,
  updateConnector,
} from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { Connector, ConnectorBase } from "@/lib/types";
import { useState } from "react";

interface UseConnectorsOpsReturn {
  isLoading: boolean;
  handleUnlinkCredential: (
    connectorId?: number,
    credentialId?: number
  ) => Promise<void>;
  handleLinkCredential: (
    connectorId?: number,
    credentialId?: number
  ) => Promise<void>;
  handleDeleteConnector: (connectorId?: number) => Promise<void>;
  handleCreateConnector: (connectorBase: ConnectorBase<{}>) => Promise<Connector<{}>>;
  handleToggleConnector: (oldConnector: Connector<{}>) =>  Promise<Connector<{}>>;
}

function verifyConnectorId(connectorId?: number): number {
  if (connectorId === undefined) {
    throw new Error("Connector ID is undefined");
  }
  return connectorId;
}

function verifyCredentialId(credentialId?: number): number {
  if (credentialId === undefined) {
    throw new Error("Credential ID is undefined");
  }
  return credentialId;
}

function verifyOrganizationId(organizationId?: string | null): string {
  if (organizationId === undefined || organizationId === null) {
    throw new Error("Organization ID is undefined");
  }
  return organizationId;
}


export function useConnectorsOps(organizationId: string| undefined | null): UseConnectorsOpsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();

  const handleDeleteConnector = async (
    connectorId?: number,
  ) => {
    setIsLoading(true);

    try {
      const validConnectorId = verifyConnectorId(connectorId);
      const validOrganizationId = verifyOrganizationId(organizationId);

      await deleteConnector(
        axiosInstance, 
        validConnectorId,
        validOrganizationId,
      );
      publish({
        variant: "success",
        text: "Successfully deleted connector!",
      });
    } catch (error: any) {
      publish({
        variant: "danger",
        text: "Failed to deleted connector!",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConnector = async (
    connectorBase: ConnectorBase<{}>,
  ) => {
    setIsLoading(true);
    try {
      const validOrganizationId = verifyOrganizationId(organizationId);

      const connector = await createConnector(
        axiosInstance, 
        connectorBase,
        validOrganizationId,
      );
      return connector;
    } catch (error: any) {
      publish({
        variant: "danger",
        text: "Failed to Enable Connector!",
      })
      throw new Error("Failed to create connector"); 
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleLinkCredential = async (
    connectorId?: number,
    credentialId?: number,
  ) => {
    setIsLoading(true);
    try {
      const validConnectorId = verifyConnectorId(connectorId);
      const validCredentialId = verifyCredentialId(credentialId);
      const validOrganizationId = verifyOrganizationId(organizationId);

      await linkCredential(
        axiosInstance, 
        validConnectorId, 
        validCredentialId,
        validOrganizationId,
      );
      publish({
        variant: "success",
        text: "Successfully Enabled Connector!",
      });
    } catch (error: any) {
      publish({
        variant: "danger",
        text: "Failed to Enable Connector!",
      });
    } finally {
      setIsLoading(false);
    }
  };


  const handleUnlinkCredential = async (
    connectorId?: number,
    credentialId?: number,
  ) => {
    setIsLoading(true);

    try {
      const validConnectorId = verifyConnectorId(connectorId);
      const validCredentialId = verifyCredentialId(credentialId);
      const validOrganizationId = verifyOrganizationId(organizationId);
      await unlinkCredential(
        axiosInstance,
        validConnectorId,
        validCredentialId,
        validOrganizationId,
      );

      publish({
        variant: "success",
        text: "Successfully disconnected.",
      });
    } catch (error: any) {
      publish({
        variant: "danger",
        text: "Failed to disconnect"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleConnector = async (
    oldConnector: Connector<{}>,
  ) => {
    setIsLoading(true);
    try {
      const validOrganizationId = verifyOrganizationId(organizationId);

      const toggledConnector: Connector<{}> = {
        ...oldConnector,
        disabled: !oldConnector.disabled,
      }

      const updatedConnector = await updateConnector(
        axiosInstance, 
        toggledConnector,
        validOrganizationId,
      );
      publish({
        variant: "success",
        text: `Successfully ${oldConnector.disabled ? "enabled" : "disabled"} connector`,
      });
      return updatedConnector;
    } catch (error: any) {
      publish({
        variant: "danger",
        text: `Failed to ${oldConnector.disabled ? "enable" : "disable"} connector`
      });
      throw new Error(`Failed to ${oldConnector.disabled ? "enable" : "disable"} connector`); 
    } finally {
      setIsLoading(false);
    }

  }


  return {
    isLoading,
    handleUnlinkCredential,
    handleLinkCredential,
    handleDeleteConnector,
    handleCreateConnector,
    handleToggleConnector,
  };
}
