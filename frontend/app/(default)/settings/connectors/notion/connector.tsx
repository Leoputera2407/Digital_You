import AuthButton from "@/components/ui/AuthButton";
import { Collapsible } from "@/components/ui/Collapsible";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import { NotionIcon } from "@/components/ui/Icon";
import { useOrganization } from "@/lib/context/orgProvider";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import { AnyCredentialJson, Connector, ConnectorBase, ConnectorIndexingStatus, Credential } from "@/lib/types";
import { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { useNotionConnectors } from "./hook";

interface NotionConnectorProps {
  user: any | undefined;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<AnyCredentialJson>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

const NotionConnector: React.FC<NotionConnectorProps> = ({
  user,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { currentOrganization } = useOrganization();

  const {
    isLoading: isNotionAuthenticating,
    handleAuthenticate: handleNotionAuthenticate,
    notionConnectorIndexingStatus,
    notionPublicCredential,
    notionConnector,
    credentialIsLinked: isNotionCredentialLinked,
  } = useNotionConnectors({
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
    organizationId: currentOrganization?.id,
  });

  const {
    revalidateCredentials,
    revalidateIndexingStatus,
  } = useConnectorData(currentOrganization?.id)

  const {
    isLoading: isLoadingConnectorOps,
    handleCreateConnector,
    handleUnlinkCredential,
    handleLinkCredential,
  } = useConnectorsOps(
    currentOrganization?.id
  );

  const handleToggleOpen = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const handleCreateLinkConnector = async () => {
    const connectorBase: ConnectorBase<{}> = {
        name: "NotionConnector",
        input_type: "load_state",
        source: "notion",
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
            notionPublicCredential?.id,
        );
        revalidateIndexingStatus();
        revalidateCredentials();
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
            <NotionIcon />
            <span>Notion</span>
          </div>
          { !isConnectorCredentialLoading &&
            notionConnectorIndexingStatus &&
            notionPublicCredential &&
            isNotionCredentialLinked && (
              <ConnectorStatus
                connectorIndexingStatus={notionConnectorIndexingStatus}
                hasCredentialsIssue={
                  notionConnectorIndexingStatus.connector.credential_ids
                    .length === 0
                }
                user={user}
                onUpdate={() => {
                  revalidateIndexingStatus();
                }}
              />
            )}
        </div>

        {isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : notionPublicCredential === undefined ? (
          <AuthButton
            className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
            onClick={handleNotionAuthenticate}
            isLoading={isNotionAuthenticating}
          >
            Authenticate
          </AuthButton>
        ) : notionConnectorIndexingStatus === undefined &&
          notionConnector === undefined ? (
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
                isNotionCredentialLinked
                ? async (event) => {
                    event.preventDefault();
                    try {
                        await handleUnlinkCredential(
                            notionConnector?.id,
                            notionPublicCredential?.id,
                        );
                        revalidateIndexingStatus();
                        revalidateCredentials();
                    } catch (e) {
                        console.error(e);
                    }
                }
                : async (event) => {
                    event.preventDefault();
                    try {
                        await handleLinkCredential(
                            notionConnector?.id,
                            notionPublicCredential?.id,
                        );
                        revalidateIndexingStatus();
                        revalidateCredentials();
                    } catch (e) {
                        console.error(e);
                    }
                }
            }
            isLoading={isLoadingConnectorOps}
          >
            {isNotionCredentialLinked ? "Disable" : "Enable?"}
          </AuthButton>
        )}
      </div>
    </Collapsible>
  );
};

export default NotionConnector;
