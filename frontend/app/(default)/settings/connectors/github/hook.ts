import {
  AnyCredentialJson,
  Connector,
  ConnectorIndexingStatus,
  Credential,
  GithubConfig,
  GithubCredentialJson,
} from "@/lib/types";

export interface UseGithubManyConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
}

export interface UseGithubManyConnectorsReturn {
  githubConnectorsInfo:
    |{
        connector: Connector<GithubConfig>;
        indexingStatus: ConnectorIndexingStatus<GithubConfig>;
        credentialIsLinked: boolean;
      }[]
    | undefined;
  githubPublicCredential: Credential<GithubCredentialJson> | undefined;
  githubConnectorIndexingStatuses: ConnectorIndexingStatus<GithubConfig>[] | undefined;
}

function isGithubCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<GithubCredentialJson> {
  return credential.credential_json.hasOwnProperty("github_access_token");
}

export function useGithubManyConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
}: UseGithubManyConnectorsProps): UseGithubManyConnectorsReturn {
  const githubPublicCredential = credentialsData?.find(
    (credential): credential is Credential<GithubCredentialJson> =>
      isGithubCredentialJson(credential) &&
      !!credential.credential_json.github_access_token &&
      credential.public_doc
  );

  let githubConnectorsInfo;

  if (connectorIndexingStatuses) {
    const info = connectorIndexingStatuses
      .filter((indexingStatus) => indexingStatus.connector.source === "github")
      .map((indexingStatus) => {
        const connector = connectorsData?.find(
          (connector) => connector.id === indexingStatus.connector.id
        );

        if (!connector) {
          console.log(
            `Connector with id ${indexingStatus.connector.id} not found.`
          );
          return null;
        }

        return {
          connector,
          indexingStatus,
          credentialIsLinked:
            githubPublicCredential &&
            indexingStatus.connector.credential_ids.includes(
              githubPublicCredential.id
            ),
        };
      })
      .filter(
        (
          info
        ): info is {
          connector: Connector<GithubConfig>;
          indexingStatus: ConnectorIndexingStatus<any>;
          credentialIsLinked: boolean;
        } => info !== null
      );

    if (info.length > 0) {
      githubConnectorsInfo = info;
    }
  }

  const githubConnectorIndexingStatuses = connectorIndexingStatuses?.filter(
    (indexingStatus) => indexingStatus.connector.source === "github"
  );

  return {
    githubConnectorsInfo,
    githubPublicCredential,
    githubConnectorIndexingStatuses,
  };
}
