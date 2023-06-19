import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { setupNotionOAuth } from "@/lib/notion";
import {
    AnyCredentialJson,
    Connector,
    ConnectorIndexingStatus,
    Credential,
    NotionCredentialJson,
} from "@/lib/types";
import { useRouter } from "next/navigation";
import { useState } from "react";

export interface UseNotionConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<AnyCredentialJson>[] | undefined;
  userId: string | undefined;
}

export interface UseNotionConnectorsReturn {
  isLoading: boolean;
  handleAuthenticate: () => Promise<void>;
  notionConnectorIndexingStatus:
    | ConnectorIndexingStatus<any>
    | undefined;
  notionPublicCredential:
    | Credential<NotionCredentialJson>
    | undefined;
  notionConnector: Connector<AnyCredentialJson> | undefined;
  credentialIsLinked: boolean;
}

function isNotionCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<NotionCredentialJson> {
  return credential.credential_json.hasOwnProperty("notion_access_tokens");
}

export function useNotionConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  userId,
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

  const handleAuthenticate = async () => {
    setIsLoading(true);
    try {
       if (userId === undefined) {
            throw new Error("User ID is undefined");
       }
      
      const [authUrl, errorMsg] = await setupNotionOAuth({
        axiosInstance,
        userId,
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
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    handleAuthenticate,
    notionConnectorIndexingStatus,
    notionPublicCredential,
    notionConnector,
    credentialIsLinked,
  };
}
