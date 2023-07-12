'use client';
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import AuthButton from "@/components/ui/authButton";
import { Collapsible } from "@/components/ui/collapsible";
import { SlackIcon } from "@/components/ui/icon";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import { useToast } from "@/lib/hooks/useToast";
import {
  AnyCredentialJson,
  Connector,
  ConnectorIndexingStatus,
  Credential,
  OrganizationBase,
} from "@/lib/types";
import { useEffect, useRef, useState } from "react";
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
  const { publish } = useToast();

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

  const { revalidateConnectors, revalidateIndexingStatus } = useConnectorData(
    currentOrganization?.id
  );

  const { 
    isLoading: isLoadingConnectorOps, 
    handleToggleConnector,
    handleDeleteConnector,
  } =
    useConnectorsOps(currentOrganization?.id);

  const handleToggleOpen = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const slackErrorPublishedRef = useRef(false);

  useEffect(() => {
    let url = new URL(window.location.href);
    let searchParams = new URLSearchParams(url.search);
    let connectorType = searchParams.get('connector_type');
    let status = searchParams.get('status');
    let errorMessage = searchParams.get('error_message');

    async function deleteAndRefresh(slackConnector: Connector<any>) {
      // delete connector
      await handleDeleteConnector(slackConnector.id, true);
      
      // remove query parameters from URL
      const location = window.location;
      const cleanUrl = `${location.protocol}//${location.host}${location.pathname}`;
      window.history.pushState({}, '', cleanUrl);
    }

    if (connectorType === 'slack' && status && errorMessage && slackConnector !== undefined ) {
      slackErrorPublishedRef.current = true;
      publish({
        variant: "danger",
        text: "Failed to connect to Slack: " + errorMessage,
      });
      deleteAndRefresh(slackConnector);
    }
  }, [slackConnector]);
  

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={handleToggleOpen}
      className="w-full space-y-2"
    >
      <div className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-2">
          <SlackIcon />
          <span>Slack</span>
        </div>
        <div className="flex items-center space-x-4">
          {!isConnectorCredentialLoading &&
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

          {isConnectorCredentialLoading ? (
            <div className="animate-spin mr-2">
              <FaSpinner className="h-5 w-5 text-white" />
            </div>
          ) : (slackPublicCredential === undefined &&
            slackConnectorIndexingStatus === undefined) ||
            slackConnector === undefined ? (
            <AuthButton
              className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
              onClick={handleSlackAuthenticate}
              isLoading={isSlackAuthenticating}
            >
              Connect
            </AuthButton>
          ) : (
            <AuthButton
              className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
              onClick={async (event) => {
                event.preventDefault();
                try {
                  await handleToggleConnector(slackConnector!);
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
              ) : slackConnector?.disabled ? (
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

export default SlackConnector;
