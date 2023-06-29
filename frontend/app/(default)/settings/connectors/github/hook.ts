import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { AnyCredentialJson, Connector, ConnectorIndexingStatus, Credential, GithubCredentialJson } from "@/lib/types";
import { useRouter } from "next/router";
import { useState } from "react";

export interface UseGithubConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<AnyCredentialJson>[] | undefined;
  userId: string | undefined;
}

export interface UseGithubConnectorsReturn {
  isLoading: boolean;
  handleAuthenticate: (token: string) => Promise<void>;
  githubConnectorIndexingStatus: ConnectorIndexingStatus<any> | undefined;
  githubPublicCredential: Credential<GithubCredentialJson> | undefined;
  githubConnector: Connector<AnyCredentialJson> | undefined;
  credentialIsLinked: boolean;
}

function isGithubCredentialJson(
    credential: Credential<AnyCredentialJson>
  ): credential is Credential<GithubCredentialJson> {
    return credential.credential_json.hasOwnProperty("github_access_tokens");
  }

export function UseGithubConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  userId,
}: UseGithubConnectorsProps): UseGithubConnectorsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const router = useRouter();

   // This returns the first cred that matches the criteria
   const githubPublicCredential = credentialsData?.find(
    (credential): credential is Credential<GithubCredentialJson> =>
    isGithubCredentialJson(credential) &&
      !!credential.credential_json.github_access_tokens &&
      credential.public_doc
  );

 

  const githubConnector = connectorsData?.find(
    (connector) => connector.source === "github"
  );
  const githubConnectorIndexingStatuses = connectorIndexingStatuses?.filter(
    (connectorIndexingStatus) => connectorIndexingStatus.connector.source === "github"
  );

  const githubConnectorIndexingStatus = githubConnectorIndexingStatuses?.[0];

  const credentialIsLinked =
    githubConnectorIndexingStatus !== undefined &&
    githubPublicCredential !== undefined &&
    githubConnectorIndexingStatus.connector.credential_ids.includes(
        githubPublicCredential.id
    );

  const handleAuthenticate = async (token: string) => {
    setIsLoading(true);
    try {
      if (userId === undefined) {
        throw new Error("User ID is undefined");
      }

      // Add your authentication logic here using the token

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
    handleAuthenticate,
    githubConnectorIndexingStatus,
    githubPublicCredential,
    githubConnector,
    credentialIsLinked,
  };
}