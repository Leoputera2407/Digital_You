import { createCredential } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
  AnyCredentialJson,
  Connector,
  ConnectorIndexingStatus,
  Credential,
  NotionConfig,
  NotionCredentialJson,
} from "@/lib/types";
import type { Axios, AxiosResponse } from "axios";
import { useRouter } from "next/navigation";
import { useState } from "react";

export interface UseNotionConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  organizationId: string | undefined;
}

export interface UseNotionConnectorsReturn {
  isLoading: boolean;
  handleConnect: () => Promise<void>;
  notionConnectorIndexingStatus:
    | ConnectorIndexingStatus<NotionConfig>
    | undefined;
  notionPublicCredential:
    | Credential<NotionCredentialJson>
    | undefined;
  notionConnector: Connector<NotionConfig> | undefined;
  credentialIsLinked: boolean;
}
interface SetupNotionArgs {
  axiosInstance: Axios;
  isPublic: boolean;
  organizationId: string;
}

function isNotionCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<NotionCredentialJson> {
  return credential.credential_json.hasOwnProperty("notion_access_tokens");
}

const setupNotionOAuth = async ({
    axiosInstance,
    isPublic,
    organizationId,
  }: SetupNotionArgs): Promise<[string | null, string]> => {
    let authorizationUrlResponse: AxiosResponse<{auth_url: string}>;
  
    try {
      const credential = await createCredential({
        axiosInstance,
        publicDoc: isPublic,
        credentialJson: {},
        organizationId
      });
      authorizationUrlResponse = await axiosInstance.get(
        `/api/connector/${organizationId}/notion/authorize/${credential.id}`
      );
      const { data: authorizationUrlJson } = authorizationUrlResponse;
      return [authorizationUrlJson.auth_url, ""];
    } catch (error: any) {
        const status = error.response?.status || 500;
        return [null, `Failed to create credential - ${status}`];
    }
  };

export function useNotionConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  organizationId,
}: UseNotionConnectorsProps): UseNotionConnectorsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const router = useRouter();
  
  // This returns the first cred that matches the criteria
  const notionPublicCredential = credentialsData?.find(
    (credential): credential is Credential<NotionCredentialJson> =>
      isNotionCredentialJson(credential) &&
      !!credential.credential_json.notion_access_tokens &&
      credential.public_doc
  );

  const notionConnector = connectorsData?.find(
    (connector) => connector.source === "notion"
  );
  const notionConnectorIndexingStatuses =
    connectorIndexingStatuses?.filter(
      (connectorIndexingStatus) =>
        connectorIndexingStatus.connector.source === "notion"
    );

  // Sorted by most recent
  const notionConnectorIndexingStatus =
    notionConnectorIndexingStatuses?.[0];

  const credentialIsLinked =
    notionConnectorIndexingStatus !== undefined &&
    notionPublicCredential !== undefined &&
    notionConnectorIndexingStatus.connector.credential_ids.includes(
      notionPublicCredential.id
    );

  const handleConnect = async () => {
    setIsLoading(true);
    try {
       if (organizationId === undefined) {
            throw new Error("Org ID is undefined");
       }
      
      const [authUrl, errorMsg] = await setupNotionOAuth({
        axiosInstance,
        organizationId: organizationId,
        isPublic: true,
      });

      if (authUrl) {
        router.push(authUrl);
        return;
      }

      publish({
        variant: "danger",
        text: errorMsg,
      });
    } catch (error: any){
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
    notionConnectorIndexingStatus,
    notionPublicCredential,
    notionConnector,
    credentialIsLinked,
  };
}
