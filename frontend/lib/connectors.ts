import type { Axios } from "axios";
import { Connector, ConnectorBase } from "./types";

export async function createConnector<T>(
  axiosInstance: Axios,
  connector: ConnectorBase<T>,
  userId: string
): Promise<Connector<T>> {

  const response = await axiosInstance.post(`/api/connector/create?supabase_user_id=${userId}`, {
    ...connector
  });
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to create connector - ${response.status}`);
  }
  return response.data;
}

export async function getConnectorById<T>(
  axiosInstance: Axios,
  connectorId: number,
  userId: string
): Promise<Connector<T>> {
  const response = await axiosInstance.get(`/api/connector/${connectorId}`, {
    params: {
      supabase_user_id: userId,
    },
  });
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to get connector - ${response.status}`);
  }
  return response.data;
}

export async function updateConnector<T>(
  axiosInstance: Axios,
  connector: Connector<T>,
  userId: string
): Promise<Connector<T>> {

  const response = await axiosInstance.patch(`/api/connector/${connector.id}`, {
    ...connector,
    supabase_user_id: userId,
  });
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to delete connector - ${response.status}`);
  }
  return response.data;
}

export async function deleteConnector<T>(
  axiosInstance: Axios,
  connectorId: number,
  userId: string
): Promise<Connector<T>> {
  const response = await axiosInstance.delete(`/api/connector/${connectorId}`, {
    data: {
      supabase_user_id: userId,
    },
  });
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to delete connector - ${response.status}`);
  }
  return response.data;
}

export async function deleteCredential<T>(
  axiosInstance: Axios,
  credentialId: number,
  userId: string
) {
  const response = await axiosInstance.delete(
    `/api/connector/credential/${credentialId}`,
    {
      params: {
        supabase_user_id: uUserId,
      },
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to delete credential - ${response.status}`);
  }
  return response.data;
}

export async function linkCredential<T>(
  axiosInstance: Axios,
  connectorId: number,
  credentialId: number,
  userId: string
) {
  const response = await axiosInstance.put(
    `/api/connector/${connectorId}/credential/${credentialId}`,
    {},
    {
      params: {
        supabase_user_id: userId,
      },
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to link connector to credential - ${response.status}`
    );
  }
  return response.data;
}

export async function unlinkCredential<T>(
  axiosInstance: Axios,
  connectorId: number,
  credentialId: number,
  userId: string
) {
  const response = await axiosInstance.delete(
    `/api/connector/${connectorId}/credential/${credentialId}`,
    {
      params: {
        supabase_user_id: userId,
      },
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to unlink connector from credential - ${response.status}`
    );
  }
  return response.data;
}

