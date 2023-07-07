import AuthButton from "@/components/ui/AuthButton";
import { Collapsible } from "@/components/ui/Collapsible";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import { NotionIcon } from "@/components/ui/Icon";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import { AnyCredentialJson, Connector, ConnectorBase, ConnectorIndexingStatus, Credential, OrganizationBase } from "@/lib/types";
import { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { useNotionConnectors } from "./hook";

interface NotionConnectorProps {
  currentOrganization: OrganizationBase | null;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

const NotionConnector: React.FC<NotionConnectorProps> = ({
  currentOrganization,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const {
    isLoading: isNotionAuthenticating,
    handleConnect: handleNotionAuthenticate,
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
    handleLinkCredential,
    handleToggleConnector,
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
        refresh_freq: 60 * 30, // 30 minutes
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
            Connect
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
          onClick={async (event) => {
            event.preventDefault();
            try {
              await handleToggleConnector(
                notionConnector!,
              );
              revalidateIndexingStatus();
            } catch (e) {
              console.error(e);
            }
          }}
          isLoading={isLoadingConnectorOps}
        >
          {notionConnector?.disabled ? "Enable" : "Disable"}
        </AuthButton>
        )}
      </div>
    </Collapsible>
  );
};

export default NotionConnector;
