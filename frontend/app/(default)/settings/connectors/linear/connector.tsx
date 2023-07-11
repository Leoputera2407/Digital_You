"use client";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import AuthButton from "@/components/ui/authButton";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { LinearIcon } from "@/components/ui/icon";
import { fetchLinearOrgAndTeam } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import {
    AnyCredentialJson,
    Connector,
    ConnectorBase,
    ConnectorIndexingStatus,
    Credential,
    LinearConfig,
    OrganizationBase,
} from "@/lib/types";
import { ChevronsUpDown } from "lucide-react";
import { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { useLinearManyConnectors } from "./hook";

interface LinearConnectorProps {
  currentOrganization: OrganizationBase | null;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

const linearConnectorNameBuilder = (
  workspace: string,
  teamName: string
): string => {
  return `LinearConnector-${workspace}/${teamName}`;
};


const LinearConnector: React.FC<LinearConnectorProps> = ({
  currentOrganization,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { axiosInstance } = useAxios();

  const {
    isLoading: isLinearAuthenticating,
    handleConnect: handleLinearAuthenticate,
    linearConnectorsInfo,
    linearPublicCredential,
    linearConnectorIndexingStatuses,
  } = useLinearManyConnectors({
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
    organizationId: currentOrganization?.id,
  });

  const {
    revalidateCredentials,
    revalidateConnectors,
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

  const handleCreateLinkConnector = async (credentialId: number) => {
    if (!currentOrganization) {
      throw new Error("No current organization!");
    }
    if (!linearPublicCredential) {
      throw new Error("No linear public credential!");
    }

    // Fetch the Linear organization and teams
    const linearOrgAndTeams = await fetchLinearOrgAndTeam(
      axiosInstance,
      currentOrganization?.id,
      linearPublicCredential?.id
    );

    let currentTeam: {
      id: string;
      name: string;
    } | null = null;

    try {
      // Iterate over each team
      for (const team of linearOrgAndTeams.teams) {
        currentTeam = team;
        const connectorBase: ConnectorBase<LinearConfig> = {
          name: linearConnectorNameBuilder(linearOrgAndTeams.name, team.name),
          input_type: "load_state",
          source: "linear",
          connector_specific_config: {
            team_id: team.id,
            team_name: team.name,
            workspace: linearOrgAndTeams.name,
          },
          refresh_freq: 60 * 30, // 30 minutes
          disabled: false,
        };

        const connector = await handleCreateConnector(connectorBase);
        await handleLinkCredential(connector.id, credentialId);
      }
    } catch (error: any) {
      throw new Error(
        `Failed to Enable Connector for team ${currentTeam?.name}!`
      );
    } finally {
      revalidateCredentials();
      revalidateIndexingStatus();
      revalidateConnectors();
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
        {linearConnectorIndexingStatuses &&
         linearConnectorIndexingStatuses.length > 0 &&
         !isConnectorCredentialLoading &&
         linearPublicCredential && (
                <CollapsibleTrigger asChild>
                  <AuthButton className="hover:bg-accent hover:text-accent-foreground p-1">
                    <ChevronsUpDown className="h-6 w-6" />
                    <span className="sr-only">Toggle</span>
                  </AuthButton>
                </CollapsibleTrigger>
              )}
          
          <LinearIcon />
          <span>Linear</span>
          {
            linearConnectorsInfo &&
            linearConnectorsInfo.length > 0 &&
            linearConnectorIndexingStatuses && 
            linearConnectorIndexingStatuses.length > 0 && 
            (
                <Badge className="bg-orange-200 text-orange-800">
                    <span>Organization: {linearConnectorsInfo[0].connector.connector_specific_config.workspace}</span>
                </Badge>
            )}
        </div>
        {isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : linearPublicCredential === undefined ? (
          <AuthButton
            className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
            onClick={handleLinearAuthenticate}
          >
            Connect
          </AuthButton>
        ) : linearConnectorIndexingStatuses === undefined ||
          linearConnectorIndexingStatuses.length === 0 ? (
          <AuthButton
            className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
            onClick={()=>handleCreateLinkConnector(linearPublicCredential!.id)}
          >
            Enable?
          </AuthButton>
        ) : (
          <div className="font-mono text-sm">
            <span className="font-bold">Access Token:</span>
            <span className="ml-2 text-gray-400">
              {linearPublicCredential!.credential_json.linear_access_tokens}
            </span>
          </div>
        )}
      </div>

      <CollapsibleContent className="space-y-2">
        {linearConnectorsInfo &&
          linearConnectorsInfo.length > 0 &&
          linearConnectorIndexingStatuses &&
          linearConnectorIndexingStatuses.length > 0 &&
          !isConnectorCredentialLoading &&
          linearPublicCredential &&
          linearConnectorsInfo.map((connectorInfo, i) => {
            const { connector, indexingStatus, credentialIsLinked } =
              connectorInfo;
            const {team_name } =
              connector.connector_specific_config;

            return (
              <div
                className="rounded-md border px-4 py-3 font-mono text-sm mb-4"
                key={i}
              >
                <div className="flex items-center justify-between space-x-4">
                  <span>
                    {team_name}
                  </span>

                  {!isConnectorCredentialLoading &&
                    indexingStatus &&
                    credentialIsLinked && (
                      <div className="flex items-center space-x-4">
                        <ConnectorStatus
                          connectorIndexingStatus={indexingStatus}
                          hasCredentialsIssue={
                            indexingStatus.connector.credential_ids.length === 0
                          }
                        />
                        <AuthButton
                          className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
                          onClick={async (event) => {
                            event.preventDefault();
                            try {
                              await handleToggleConnector(connector);
                              revalidateConnectors();
                              revalidateIndexingStatus();
                            } catch (e) {
                              console.error(e);
                            }
                          }}
                          disabled={isLoadingConnectorOps}
                        >
                          {isLoadingConnectorOps ? (
                            <div className="animate-spin mr-2">
                              <FaSpinner className="h-5 w-5 text-white" />
                            </div>
                          ) : connector.disabled ? (
                            "Enable"
                          ) : (
                            "Disable"
                          )}
                        </AuthButton>
                      </div>
                    )}
                </div>
              </div>
            );
          })}
        
      </CollapsibleContent>
    </Collapsible>
  );
};

export default LinearConnector;
