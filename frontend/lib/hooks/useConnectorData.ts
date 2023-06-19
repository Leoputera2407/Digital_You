import { fetcher } from "@/lib/fetcher";
import { Connector, ConnectorIndexingStatus, Credential } from "@/lib/types";
import useSWR from "swr";

type UseConnectorResponse<T> = {
  isLoading: boolean,
  isCredentialsError: boolean,
  isConnectorIndexingStatusesError:boolean,
  isConnectorsError: boolean,
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined,
  credentialsData: Credential<T>[] | undefined,
  connectorsData: Connector<T>[] | undefined,
};

export const useConnectorData = <T>(user: any): UseConnectorResponse<T> => {
  
  const {
    data: connectorIndexingStatuses,
    isLoading: isConnectorIndexingStatusesLoading,
    error: isConnectorIndexingStatusesError,
  } = useSWR<ConnectorIndexingStatus<any>[]>(
    `/api/connector/indexing-status?supabase_user_id=${user?.id}`,
    fetcher
  );
  const {
    data: credentialsData,
    isLoading: isCredentialsLoading,
    error: isCredentialsError,
  } = useSWR<Credential<T>[]>(
    `/api/connector/credential?supabase_user_id=${user?.id}`,
    fetcher
  );
  const {
    data: connectorsData,
    isLoading: isConnectorsLoading,
    error: isConnectorsError,
  } = useSWR<Connector<T>[]>(
    `/api/connector/list?supabase_user_id=${user?.id}`,
    fetcher
  );
  
  return {
    isLoading: isConnectorIndexingStatusesLoading || isCredentialsLoading || isConnectorsLoading,
    isCredentialsError,
    isConnectorIndexingStatusesError,
    isConnectorsError,
    connectorIndexingStatuses,
    credentialsData,
    connectorsData
  };
};