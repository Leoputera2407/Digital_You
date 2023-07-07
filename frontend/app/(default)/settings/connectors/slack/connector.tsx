import AuthButton from "@/components/ui/AuthButton";
import { Collapsible } from "@/components/ui/Collapsible";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import { SlackIcon } from "@/components/ui/Icon";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import { AnyCredentialJson, Connector, ConnectorIndexingStatus, Credential, OrganizationBase } from "@/lib/types";
import { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { useSlackConnectors } from "./hook";

interface SlackConnectorProps {
  currentOrganization: OrganizationBase | null;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

const SlackConnector: React.FC<SlackConnectorProps> = ({
  currentOrganization,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const {
    isLoading: isSlackAuthenticating,
    handleConnect: handleSlackAuthenticate,
    slackConnectorIndexingStatus,
    slackPublicCredential,
    slackConnector,
    credentialIsLinked: isSlackCredentialLinked,
  } = useSlackConnectors({
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
    organizationId: currentOrganization?.id,
  });

  const {
    revalidateIndexingStatus,
  } = useConnectorData(currentOrganization?.id)

  const {
    isLoading: isLoadingConnectorOps,
    handleToggleConnector,
  } = useConnectorsOps(
    currentOrganization?.id
  );

  const handleToggleOpen = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
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
            <SlackIcon />
            <span>Slack</span>
          </div>
          { !isConnectorCredentialLoading &&
            slackConnectorIndexingStatus &&
            slackPublicCredential &&
            isSlackCredentialLinked && (
              <ConnectorStatus
                connectorIndexingStatus={slackConnectorIndexingStatus}
                hasCredentialsIssue={
                  slackConnectorIndexingStatus.connector.credential_ids
                    .length === 0
                }
              />
            )}
        </div>

        {isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : slackPublicCredential === undefined &&
            slackConnectorIndexingStatus === undefined &&
            slackConnector === undefined
        ? (
          <AuthButton
            className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
            onClick={handleSlackAuthenticate}
            isLoading={isSlackAuthenticating}
          >
            Connect
          </AuthButton>
        ) : (
          <AuthButton
          className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
          onClick={async (event) => {
            event.preventDefault();
            try {
              await handleToggleConnector(
                slackConnector!,
              );
              revalidateIndexingStatus();
            } catch (e) {
              console.error(e);
            }
          }}
          isLoading={isLoadingConnectorOps}
        >
          {slackConnector?.disabled ? "Enable" : "Disable"}
        </AuthButton>
        )}
      </div>
    </Collapsible>
  );
};

export default SlackConnector;
