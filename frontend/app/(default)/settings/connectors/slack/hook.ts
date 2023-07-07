import { createConnector } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
  AnyCredentialJson,
  Connector,
  ConnectorBase,
  ConnectorIndexingStatus,
  Credential,
  SlackConfig,
  SlackCredentialJson,
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
  return credential.credential_json.hasOwnProperty("notion_access_tokens");
}

const setupSlackOAuth = async ({
  axiosInstance,
  isPublic,
  organizationId,
}: SetupSlackArgs): Promise<[boolean, string?]> => {
   /*
      // TODO: For now, all creds made are public in the server-side, make that configurable
      All creds creation + linking are done server-side 
      Server-side, however, assumes that a Connector is already made. 
      So, we need to make connector before calling the server.
    */
  try {
    const connectorBase: ConnectorBase<{}> = {
      name: "SlackConnector",
      input_type: "load_state",
      source: "slack",
      connector_specific_config: {},
      refresh_freq: 60 * 30, // 30 minutes
      disabled: false,
    };
    const connector = await createConnector(
      axiosInstance,
      connectorBase,
      organizationId
    );

    await axiosInstance.get(`/api/slack/install/${organizationId}`);
    return [true];
  } catch (error: any) {
    const status = error.response?.status || 500;
    console.log(`Failed to oauth for Slack - ${status}`);
    return [false, `Failed to oauth for Slack - ${status}`];
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
