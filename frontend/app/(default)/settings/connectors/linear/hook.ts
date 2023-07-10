"use client";
import { createCredential } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
    AnyCredentialJson,
    Connector,
    ConnectorIndexingStatus,
    Credential,
    LinearConfig,
    LinearCredentialJson,
} from "@/lib/types";
import { Axios, AxiosResponse } from 'axios';
import { useRouter } from "next/navigation";
import { useState } from "react";

export interface UseLinearManyConnectorsProps {
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  organizationId: string | undefined;
}

export interface UseLinearManyConnectorsReturn {
    isLoading: boolean;
    linearConnectorsInfo:
        | {
            connector: Connector<LinearConfig>;
            indexingStatus: ConnectorIndexingStatus<LinearConfig>;
            credentialIsLinked: boolean;
        }[]
        | undefined;
    handleConnect: () => Promise<void>;
    linearPublicCredential: Credential<LinearCredentialJson> | undefined;
    linearConnectorIndexingStatuses:
        | ConnectorIndexingStatus<LinearConfig>[]
        | undefined;
}

interface SetupLinearArgs {
    axiosInstance: Axios;
    isPublic: boolean;
    organizationId: string;
}

function isLinearCredentialJson(
  credential: Credential<AnyCredentialJson>
): credential is Credential<LinearCredentialJson> {
  return credential.credential_json.hasOwnProperty("linear_access_tokens");
}

const setupLinearOAuth = async ({
    axiosInstance,
    isPublic,
    organizationId,
  }: SetupLinearArgs): Promise<[string | null, string]> => {
    let authorizationUrlResponse: AxiosResponse<{auth_url: string}>;
  
    try {
      const credential = await createCredential({
        axiosInstance,
        publicDoc: isPublic,
        credentialJson: {},
        organizationId
      });
      authorizationUrlResponse = await axiosInstance.get(
        `/api/connector/${organizationId}/linear/authorize/${credential.id}`
      );
      const { data: authorizationUrlJson } = authorizationUrlResponse;
      return [authorizationUrlJson.auth_url, ""];
    } catch (error: any) {
        const status = error.response?.status || 500;
        return [null, `Failed to create credential - ${status}`];
    }
  };


export function useLinearManyConnectors({
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  organizationId,
}: UseLinearManyConnectorsProps): UseLinearManyConnectorsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const router = useRouter();

  const linearPublicCredential = credentialsData?.find(
    (credential): credential is Credential<LinearCredentialJson> =>
      isLinearCredentialJson(credential) &&
      !!credential.credential_json.linear_access_tokens &&
      credential.public_doc
  );

  let linearConnectorsInfo;

  if (connectorIndexingStatuses) {
    const info = connectorIndexingStatuses
      .filter((indexingStatus) => indexingStatus.connector.source === "linear")
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
            linearPublicCredential &&
            indexingStatus.connector.credential_ids.includes(
              linearPublicCredential.id
            ),
        };
      })
      .filter(
        (
          info
        ): info is {
          connector: Connector<LinearConfig>;
          indexingStatus: ConnectorIndexingStatus<any>;
          credentialIsLinked: boolean;
        } => info !== null
      );

    if (info.length > 0) {
      linearConnectorsInfo = info;
    }
  }

  const linearConnectorIndexingStatuses = connectorIndexingStatuses?.filter(
    (indexingStatus) => indexingStatus.connector.source === "linear"
  );

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      if (organizationId === undefined) {
        throw new Error("Org ID is undefined");
      }

      const [authUrl, errorMsg] = await setupLinearOAuth({
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
    linearConnectorsInfo,
    handleConnect,
    linearPublicCredential,
    linearConnectorIndexingStatuses,
  };
}
