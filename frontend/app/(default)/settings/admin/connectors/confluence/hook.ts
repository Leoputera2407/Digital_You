import {
  AnyCredentialJson,
  ConfluenceConfig,
  ConfluenceCredentialJson,
  Connector,
  ConnectorIndexingStatus,
  Credential
} from "@/lib/types";

export interface UseConfluenceConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
}

export interface UseConfluenceConnectorsReturn {
  confluenceConnectorIndexingStatus:
    | ConnectorIndexingStatus<ConfluenceConfig>
    | undefined;
  confluencePublicCredential:
    | Credential<ConfluenceCredentialJson>
    | undefined;
  confluenceConnector: Connector<ConfluenceConfig> | undefined;
  credentialIsLinked: boolean;
}


function isConfluenceCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<ConfluenceCredentialJson> {
  return credential.credential_json.hasOwnProperty("confluence_access_token")
  && credential.credential_json.hasOwnProperty("confluence_username");
}

export function useConfluenceConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
}: UseConfluenceConnectorsProps): UseConfluenceConnectorsReturn {

  // This returns the first cred that matches the criteria
  const confluencePublicCredential = credentialsData?.find(
    (credential): credential is Credential<ConfluenceCredentialJson> =>
      isConfluenceCredentialJson(credential) &&
      !!credential.credential_json.confluence_access_token &&
      !!credential.credential_json.confluence_username &&
      credential.public_doc
  );

  const confluenceConnector = connectorsData?.find(
    (connector) => connector.source === "confluence"
  );
  const confluenceConnectorIndexingStatuses =
    connectorIndexingStatuses?.filter(
      (connectorIndexingStatus) =>
        connectorIndexingStatus.connector.source === "confluence"
    );

  // Sorted by most recent
  const confluenceConnectorIndexingStatus =
    confluenceConnectorIndexingStatuses?.[0];

  const credentialIsLinked =
    confluenceConnectorIndexingStatus !== undefined &&
    confluencePublicCredential !== undefined &&
    confluenceConnectorIndexingStatus.connector.credential_ids.includes(
      confluencePublicCredential.id
    );

  return {
    confluenceConnectorIndexingStatus,
    confluencePublicCredential,
    confluenceConnector,
    credentialIsLinked,
  };
}
