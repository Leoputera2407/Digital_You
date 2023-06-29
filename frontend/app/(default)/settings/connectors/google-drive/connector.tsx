import AuthButton from "@/components/ui/AuthButton";
import { Collapsible } from "@/components/ui/Collapsible";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import { GoogleDriveIcon } from "@/components/ui/Icon";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import {
  AnyCredentialJson,
  Connector,
  ConnectorBase,
  ConnectorIndexingStatus,
  Credential,
} from "@/lib/types";
import { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { useSWRConfig } from "swr";
import { useGoogleConnectors } from "./hook";

interface GoogleDriveConnectorProps {
  user: any | undefined;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<AnyCredentialJson>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

const GoogleDriveConnector: React.FC<GoogleDriveConnectorProps> = ({
  user,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const { mutate } = useSWRConfig();
  const [isOpen, setIsOpen] = useState(false);

  const {
    isLoading: isGoogleAuthenticating,
    handleAuthenticate: handleGoogleAuthenticate,
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
  });

  const {
    isLoading: isLoadingConnectorOps,
    handleCreateConnector,
    handleUnlinkCredential,
    handleLinkCredential,
  } = useConnectorsOps();

  const handleToggleOpen = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const handleCreateLinkConnector = async () => {
    const connectorBase: ConnectorBase<{}> = {
        name: "GoogleDriveConnector",
        input_type: "load_state",
        source: "google_drive",
        connector_specific_config: {},
        refresh_freq: 60 * 10, // 10 minutes
        disabled: false,
      };
      try{
        const connector = await handleCreateConnector(
          connectorBase,
        );

        await handleLinkCredential(
            connector.id,
            googleDrivePublicCredential?.id,
        );
        mutate("/api/admin/connector/indexing-status")
        mutate("/api/connector/credential")
     } catch (error: any) {
        throw new Error("Failed to Enable Connector!"); 
    };
  };


  return (
    <Collapsible
      open={isOpen}
      onOpenChange={handleToggleOpen}
      className="w-full space-y-2"
    >
      <div className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <GoogleDriveIcon />
            <span>Google Drive</span>
          </div>
          {!isAppCredentialLoading &&
            !isConnectorCredentialLoading &&
            appCredentialData &&
            googleDriveConnectorIndexingStatus &&
            googleDrivePublicCredential &&
            isGoogleCredentialLinked &&
            (
              <ConnectorStatus
                connectorIndexingStatus={googleDriveConnectorIndexingStatus}
                hasCredentialsIssue={
                  googleDriveConnectorIndexingStatus.connector.credential_ids
                    .length === 0
                }
                user={user}
                onUpdate={() => {
                  mutate("/api/connector/admin/indexing-status");
                }}
              />
            )}
        </div>

        {isAppCredentialLoading || isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : appCredentialError && !appCredentialData ? (
          <div className="text-red-500">
            Something went wrong, please contact the admin.
          </div>
        ) : googleDrivePublicCredential === undefined ? (
          <AuthButton
            className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
            onClick={handleGoogleAuthenticate}
            isLoading={isGoogleAuthenticating}
          >
            Authenticate
          </AuthButton>
        ) : googleDriveConnector === undefined  &&
            googleDriveConnectorIndexingStatus === undefined 
          ? (
          <AuthButton
            className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
            onClick={handleCreateLinkConnector}
            isLoading={isLoadingConnectorOps}
          >
            Enable?
          </AuthButton>
        ) : (
          <AuthButton
            className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
            onClick={
                isGoogleCredentialLinked
                ? async (event) => {
                    event.preventDefault();
                    try {
                        await handleUnlinkCredential(
                            googleDriveConnector?.id,
                            googleDrivePublicCredential?.id,
                        );
                        mutate("/api/connector/indexing-status")
                        mutate("/api/connector/credential")
                    } catch (e) {
                        console.error(e);
                    }
                }
                : async (event) => {
                    event.preventDefault();
                    try {
                        await handleLinkCredential(
                            googleDriveConnector?.id,
                            googleDrivePublicCredential?.id,
                        );
                        mutate("/api/connector/indexing-status")
                        mutate("/api/connector/credential")
                    } catch (e) {
                        console.error(e);
                    }
                }
            }
            isLoading={isLoadingConnectorOps}
          >
            {isGoogleCredentialLinked ? "Disable" : "Enable?"}
          </AuthButton>
        )}
      </div>
    </Collapsible>
  );
};

export default GoogleDriveConnector;
