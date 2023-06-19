import { fetcher } from "@/lib/fetcher";
import { setupGoogleDriveOAuth } from "@/lib/googleDrive";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
    AnyCredentialJson,
    Connector,
    ConnectorIndexingStatus,
    Credential,
    GoogleDriveCredentialJson,
} from "@/lib/types";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

export interface UseGoogleConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<AnyCredentialJson>[] | undefined;
  userId: string | undefined;
}

export interface UseGoogleConnectorsReturn {
  isLoading: boolean;
  handleAuthenticate: () => Promise<void>;
  googleDriveConnectorIndexingStatus:
    | ConnectorIndexingStatus<any>
    | undefined;
  googleDrivePublicCredential:
    | Credential<GoogleDriveCredentialJson>
    | undefined;
  googleDriveConnector: Connector<AnyCredentialJson> | undefined;
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

export function useGoogleConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  userId
}: UseGoogleConnectorsProps): UseGoogleConnectorsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const {
    data: appCredentialData,
    isLoading: isAppCredentialLoading,
    error: appCredentialError,
  } = useSWR<{ client_id: string }>(
    "/api/connector/google-drive/app-credential",
    fetcher
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


  const handleAuthenticate = async () => {
    setIsLoading(true);
    try {
       if (userId === undefined) {
            throw new Error("User ID is undefined");
       }
      
      const [authUrl, errorMsg] = await setupGoogleDriveOAuth({
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
    googleDriveConnectorIndexingStatus,
    googleDrivePublicCredential,
    googleDriveConnector,
    credentialIsLinked,
    appCredentialData,
    isAppCredentialLoading,
    appCredentialError,
  };
}
