import {
  createConnector,
  deleteConnector,
  linkCredential,
  unlinkCredential
} from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { ConnectorBase } from "@/lib/types";
import { useState } from "react";

function verifyConnectorId(connectorId?: number): number {
  if (connectorId === undefined) {
    throw new Error("Google Drive Connector ID is undefined");
  }
  return connectorId;
}

function verifyCredentialId(credentialId?: number): number {
  if (credentialId === undefined) {
    throw new Error("Google Drive Public Credential ID is undefined");
  }
  return credentialId;
}


export function useConnectorsOps() {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  
  const handleUnlinkCredential = async (
    connectorId?: number,
    credentialId?: number,
  ) => {
    setIsLoading(true);

    try {
      const validConnectorId = verifyConnectorId(connectorId);
      const validCredentialId = verifyCredentialId(credentialId);
      await unlinkCredential(
        axiosInstance,
        validConnectorId,
        validCredentialId,
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

  const handleDeleteConnector = async (
    connectorId?: number,
  ) => {
    setIsLoading(true);

    try {
      const validConnectorId = verifyConnectorId(connectorId);
      await deleteConnector(axiosInstance, validConnectorId);
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
      const connector = await createConnector(axiosInstance, connectorBase);
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
      await linkCredential(axiosInstance, validConnectorId, validCredentialId);
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

  return {
    isLoading,
    handleUnlinkCredential,
    handleLinkCredential,
    handleDeleteConnector,
    handleCreateConnector,
  };
}
