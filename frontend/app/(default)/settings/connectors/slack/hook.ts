import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
  AnyCredentialJson,
  Connector,
  ConnectorIndexingStatus,
  Credential,
  SlackConfig,
  SlackCredentialJson
} from "@/lib/types";
import type { Axios } from "axios";
import { useRouter } from "next/navigation";
import { useState } from "react";

export interface UseSlackConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  organizationId: string | undefined;
}

export interface UseSlackConnectorsReturn {
  isLoading: boolean;
  handleConnect: () => Promise<void>;
  slackConnectorIndexingStatus:
    | ConnectorIndexingStatus<SlackConfig>
    | undefined;
  slackPublicCredential: Credential<SlackCredentialJson> | undefined;
  slackConnector: Connector<SlackConfig> | undefined;
  credentialIsLinked: boolean;
}
interface SetupSlackArgs {
  axiosInstance: Axios;
  isPublic: boolean;
  organizationId: string;
}

function isSlackCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<SlackCredentialJson> {
  return credential.credential_json.hasOwnProperty("slack_bot_token");
}

const setupSlackOAuth = async ({
  axiosInstance,
  isPublic,
  organizationId,
}: SetupSlackArgs): Promise<[boolean, string?]> => {
  try {
     /*
      // TODO: For now, all creds made are public in the server-side, make that configurable
      
      NOTE: All creds creation + linking are done server-side 
      Server-side, however, assumes that a Connector is already made. 
      So, we need to make connector before calling the server.
    */
   
    // Get the auth url
    const response = await axiosInstance.get(`/api/slack/install/${organizationId}`);
    
    // Check if we got a successful response
    if (response.status === 200) {
      const authUrl = response.data.auth_url;
      
      /*
      Creating connector is done server-side now
      // Prepare the connector
      const connectorBase: ConnectorBase<{}> = {
        name: "SlackConnector",
        input_type: "load_state",
        source: "slack",
        connector_specific_config: {},
        refresh_freq: 60 * 30, // 30 minutes
        disabled: false,
      };
      
      // Create the connector
      const connector = await createConnector(
        axiosInstance,
        connectorBase,
        organizationId
      );
      */
      
      // Now that the connector is created, redirect to the auth url
      window.location.href = authUrl;
      
      return [true];
    } else {
      const errorMsg = `Failed to setup OAuth for Slack - ${response.status}`;
      console.error(errorMsg);
      return [false, errorMsg];
    }
  } catch (error: any) {
    const errorMsg = `Failed to setup OAuth for Slack - ${error.message}`;
    console.error(errorMsg);
    return [false, errorMsg];
  }
};


export function useSlackConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  organizationId,
}: UseSlackConnectorsProps): UseSlackConnectorsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const router = useRouter();
  // This returns the first cred that matches the criteria
  const slackPublicCredential = credentialsData?.find(
    (credential): credential is Credential<SlackCredentialJson> =>
      isSlackCredentialJson(credential) &&
      !!credential.credential_json.slack_bot_token &&
      credential.public_doc
  );

  const slackConnector = connectorsData?.find(
    (connector) => connector.source === "slack"
  );
  const slackConnectorIndexingStatuses = connectorIndexingStatuses?.filter(
    (connectorIndexingStatus) =>
      connectorIndexingStatus.connector.source === "slack"
  );

  // Sorted by most recent
  const slackConnectorIndexingStatus = slackConnectorIndexingStatuses?.[0];
  const credentialIsLinked =
    slackConnectorIndexingStatus !== undefined &&
    slackPublicCredential !== undefined &&
    slackConnectorIndexingStatus.connector.credential_ids.includes(
      slackPublicCredential.id
    );

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      if (organizationId === undefined) {
        throw new Error("Org ID is undefined");
      }

      const [success, errorMsg] = await setupSlackOAuth({
        axiosInstance,
        organizationId: organizationId,
        isPublic: true,
      });

      if (!success) {
        publish({
          variant: "danger",
          text: errorMsg!,
        });
      }
    } catch (error: any) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    handleConnect,
    slackConnectorIndexingStatus,
    slackPublicCredential,
    slackConnector,
    credentialIsLinked,
  };
}
