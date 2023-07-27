import { createCredential } from "@/lib/connectors";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
  AnyCredentialJson,
  Connector,
  ConnectorIndexingStatus,
  Credential,
  GoogleDriveCredentialJson,
} from "@/lib/types";
import type { Axios, AxiosResponse } from "axios";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

export interface UseGoogleConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  organizationId: string | undefined;
}
interface SetupGoogleDriveArgs {
  axiosInstance: Axios;
  isPublic: boolean;
  organizationId: string;
}

export interface UseGoogleConnectorsReturn {
  isLoading: boolean;
  handleConnect: () => Promise<void>;
  googleDriveConnectorIndexingStatus:
    | ConnectorIndexingStatus<{}>
    | undefined;
  googleDrivePublicCredential:
    | Credential<GoogleDriveCredentialJson>
    | undefined;
  googleDriveConnector: Connector<{}> | undefined;
  credentialIsLinked: boolean;
  appCredentialData: { client_id: string } | undefined;
  isAppCredentialLoading: boolean;
  appCredentialError: Error | undefined;
}

function isGoogleDriveCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<GoogleDriveCredentialJson> {
  return credential.credential_json.hasOwnProperty("google_drive_tokens");
}


export const setupGoogleDriveOAuth = async ({
    axiosInstance,
    isPublic,
    organizationId,
  }: SetupGoogleDriveArgs): Promise<[string | null, string]> => {
    let authorizationUrlResponse: AxiosResponse<{auth_url: string}>;
  
    try {
      const credential = await createCredential({
        axiosInstance,
        publicDoc: isPublic,
        credentialJson: {},
        organizationId
      });
      authorizationUrlResponse = await axiosInstance.get(
        `/api/connector/${organizationId}/google-drive/authorize/${credential.id}`
      );
      const { data: authorizationUrlJson } = authorizationUrlResponse;
      return [authorizationUrlJson.auth_url, ""];
    } catch (error: any) {
        const status = error.response?.status || 500;
        return [null, `Failed to create credential - ${status}`];
    }
  };

export function useGoogleConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  organizationId,
}: UseGoogleConnectorsProps): UseGoogleConnectorsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const {
    data: appCredentialData,
    isLoading: isAppCredentialLoading,
    error: appCredentialError,
  } = useSWR<{ client_id: string }>(
    organizationId ? `/api/connector/admin/${organizationId}/google-drive/app-credential` : null,
    (url) => fetcher(url, axiosInstance)
  );
  const router = useRouter();

  // This returns the first cred that matches the criteria
  const googleDrivePublicCredential = credentialsData?.find(
    (credential): credential is Credential<GoogleDriveCredentialJson> =>
      isGoogleDriveCredentialJson(credential) &&
      !!credential.credential_json.google_drive_tokens &&
      credential.public_doc
  );

  const googleDriveConnector = connectorsData?.find(
    (connector) => connector.source === "google_drive"
  );
  const googleDriveConnectorIndexingStatuses =
    connectorIndexingStatuses?.filter(
      (connectorIndexingStatus) =>
        connectorIndexingStatus.connector.source === "google_drive"
    );
 

  // Sorted by most recent
  const googleDriveConnectorIndexingStatus =
    googleDriveConnectorIndexingStatuses?.[0];
 
  const credentialIsLinked =
    googleDriveConnectorIndexingStatus !== undefined &&
    googleDrivePublicCredential !== undefined &&
    googleDriveConnectorIndexingStatus.connector.credential_ids.includes(
      googleDrivePublicCredential.id
    );


  const handleConnect = async () => {
    setIsLoading(true);
    try {
      if (organizationId === undefined) {
        throw new Error("Org ID is undefined");
      }
      const [authUrl, errorMsg] = await setupGoogleDriveOAuth({
        axiosInstance,
        organizationId,
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
    googleDriveConnectorIndexingStatus,
    googleDrivePublicCredential,
    googleDriveConnector,
    credentialIsLinked,
    appCredentialData,
    isAppCredentialLoading,
    appCredentialError,
  };
}
