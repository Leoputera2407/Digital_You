"use client"
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
import { verifyValidParamString } from "@/lib/utils";
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

export function useConnectorsOps(organizationId: string| undefined | null): UseConnectorsOpsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();

  const handleDeleteConnector = async (
    connectorId?: number,
    isSilent: boolean = false,
  ) => {
    setIsLoading(true);

    try {
      
      const validConnectorId = verifyValidParamString({
        param: connectorId,
        errorText: "Connector ID is undefined",
      });
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined",
      });
      await deleteConnector(
        axiosInstance, 
        validConnectorId,
        validOrganizationId,
      );
      if (!isSilent) {
        publish({
          variant: "success",
          text: "Successfully deleted connector!",
        });
      }
    } catch (error: any) {
      if (!isSilent) {
        publish({
          variant: "danger",
          text: "Failed to deleted connector!",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConnector = async (
    connectorBase: ConnectorBase<{}>,
  ) => {
    setIsLoading(true);
    try {
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined",
      });
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
      const validConnectorId = verifyValidParamString({
        param: connectorId,
        errorText: "Connector ID is undefined",
      });
      const validCredentialId = verifyValidParamString({
        param: credentialId,
        errorText: "Credential ID is undefined",
      });
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined",
      });
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
      const validConnectorId = verifyValidParamString({
        param: connectorId,
        errorText: "Connector ID is undefined",
      });
      const validCredentialId = verifyValidParamString({
        param: credentialId,
        errorText: "Credential ID is undefined",
      });
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined",
      });
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
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined",
      });
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
