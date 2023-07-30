import { fetcher } from "@/lib/fetcher";
import { Connector, ConnectorIndexingStatus, Credential } from "@/lib/types";
import useSWR, { mutate } from "swr";
import { useAxios } from "./useAxios";

type UseConnectorResponse<T> = {
  isLoading: boolean,
  isCredentialsError: boolean,
  isConnectorIndexingStatusesError:boolean,
  isConnectorsError: boolean,
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined,
  credentialsData: Credential<T>[] | undefined,
  connectorsData: Connector<T>[] | undefined,
  revalidateIndexingStatus: () => void,
  revalidateCredentials: () => void, 
  revalidateConnectors: () => void, 
};

export const useConnectorData = <T>(organization_id: string | null | undefined): UseConnectorResponse<T> => {
  const { axiosInstance } = useAxios();
  
  const {
    data: connectorIndexingStatuses,
    isLoading: isConnectorIndexingStatusesLoading,
    error: isConnectorIndexingStatusesError,
  } = useSWR<ConnectorIndexingStatus<any>[]>(
    organization_id ? `/api/connector/admin/${organization_id}/indexing-status` : null,
    (url) => fetcher(url, axiosInstance)
  );
  const {
    data: credentialsData,
    isLoading: isCredentialsLoading,
    error: isCredentialsError,
  } = useSWR<Credential<T>[]>(
    organization_id ? `/api/connector/admin/${organization_id}/admin-credential` : null,
    (url) => fetcher(url, axiosInstance),
  );
  const {
    data: connectorsData,
    isLoading: isConnectorsLoading,
    error: isConnectorsError,
  } = useSWR<Connector<T>[]>(
    organization_id ? `/api/connector/${organization_id}/list` : null,
    (url) => fetcher(url, axiosInstance)
  );

  const revalidateIndexingStatus = () => {
    mutate(`/api/connector/admin/${organization_id}/indexing-status`);
  };

  const revalidateCredentials = () => {
    mutate(`/api/connector/${organization_id}/credential`);
  };

  const revalidateConnectors = () => {
    mutate(`/api/connector/${organization_id}/list`);
  };
  return {
    isLoading: isConnectorIndexingStatusesLoading || isCredentialsLoading || isConnectorsLoading,
    isCredentialsError,
    isConnectorIndexingStatusesError,
    isConnectorsError,
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
    revalidateIndexingStatus,
    revalidateCredentials,
    revalidateConnectors,
  };
};