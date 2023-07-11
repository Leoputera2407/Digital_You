import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import AuthButton from "@/components/ui/authButton";
import { Collapsible } from "@/components/ui/collapsible";
import { GoogleDriveIcon } from "@/components/ui/icon";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import {
  AnyCredentialJson,
  Connector,
  ConnectorBase,
  ConnectorIndexingStatus,
  Credential,
  OrganizationBase,
} from "@/lib/types";
import { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { useGoogleConnectors } from "./hook";

interface GoogleDriveConnectorProps {
  currentOrganization: OrganizationBase | null;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<AnyCredentialJson>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

const GoogleDriveConnector: React.FC<GoogleDriveConnectorProps> = ({
  currentOrganization,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const {
    isLoading: isGoogleAuthenticating,
    handleConnect: handleGoogleAuthenticate,
    googleDriveConnectorIndexingStatus,
    googleDrivePublicCredential,
    googleDriveConnector,
    credentialIsLinked: isGoogleCredentialLinked,
    appCredentialData,
    isAppCredentialLoading,
    appCredentialError,
  } = useGoogleConnectors({
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
    organizationId: currentOrganization?.id,
  });

  const {
    revalidateConnectors,
    revalidateCredentials,
    revalidateIndexingStatus,
  } = useConnectorData(currentOrganization?.id);

  const {
    isLoading: isLoadingConnectorOps,
    handleCreateConnector,
    handleLinkCredential,
    handleToggleConnector,
  } = useConnectorsOps(currentOrganization?.id);

  const handleToggleOpen = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const handleCreateLinkConnector = async () => {
    const connectorBase: ConnectorBase<{}> = {
      name: "GoogleDriveConnector",
      input_type: "load_state",
      source: "google_drive",
      connector_specific_config: {},
      refresh_freq: 60 * 30, // 30 minutes
      disabled: false,
    };
    try {
      const connector = await handleCreateConnector(connectorBase);

      await handleLinkCredential(connector.id, googleDrivePublicCredential?.id);
      revalidateIndexingStatus();
      revalidateCredentials();
      revalidateConnectors();
    } catch (error: any) {
      throw new Error("Failed to Enable Connector!");
    }
  };

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={handleToggleOpen}
      className="w-full space-y-2"
    >
      <div className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-2">
          <GoogleDriveIcon />
          <span>Google Drive</span>
        </div>
        <div className="flex items-center space-x-4">
          {!isAppCredentialLoading &&
            !isConnectorCredentialLoading &&
            appCredentialData &&
            googleDriveConnectorIndexingStatus &&
            googleDrivePublicCredential &&
            isGoogleCredentialLinked && (
              <ConnectorStatus
                connectorIndexingStatus={googleDriveConnectorIndexingStatus}
                hasCredentialsIssue={
                  googleDriveConnectorIndexingStatus.connector.credential_ids
                    .length === 0
                }
              />
            )}

          {isAppCredentialLoading || isConnectorCredentialLoading ? (
            <div className="animate-spin mr-2">
              <FaSpinner className="h-5 w-5 text-white" />
            </div>
          ) : appCredentialError && !appCredentialData ? (
            <div className="text-red-500">
              Something went wrong, please contact the admin.
            </div>
          ) : googleDrivePublicCredential === undefined ? (
            <AuthButton
              className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
              onClick={handleGoogleAuthenticate}
              isLoading={isGoogleAuthenticating}
            >
              Connect
            </AuthButton>
          ) : googleDriveConnector === undefined &&
            googleDriveConnectorIndexingStatus === undefined ? (
            <AuthButton
              className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
              onClick={handleCreateLinkConnector}
              isLoading={isLoadingConnectorOps}
            >
              Enable?
            </AuthButton>
          ) : (
            <AuthButton
              className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
              onClick={async (event) => {
                event.preventDefault();
                try {
                  await handleToggleConnector(googleDriveConnector!);
                  revalidateConnectors();
                  revalidateIndexingStatus();
                } catch (e) {
                  console.error(e);
                }
              }}
              isLoading={isLoadingConnectorOps}
            >
              {isLoadingConnectorOps ? (
                <div className="animate-spin mr-2">
                  <FaSpinner className="h-5 w-5 text-white" />
                </div>
              ) : googleDriveConnector?.disabled ? (
                "Enable"
              ) : (
                "Disable"
              )}
            </AuthButton>
          )}
        </div>
      </div>
    </Collapsible>
  );
};

export default GoogleDriveConnector;
