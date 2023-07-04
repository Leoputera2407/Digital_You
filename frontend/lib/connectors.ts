import type { Axios } from "axios";
import { Connector, ConnectorBase } from "./types";

export async function createConnector<T>(
  axiosInstance: Axios,
  connector: ConnectorBase<T>,
  organizationId: string,
): Promise<Connector<T>> {

  const response = await axiosInstance.post(
    `/api/connector/admin/${organizationId}/create`, {
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
  organizationId: string,
): Promise<Connector<T>> {
  const response = await axiosInstance.get(
    `/api/connector/${organizationId}/${connectorId}`
    );
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to get connector - ${response.status}`);
  }
  return response.data;
}

export async function updateConnector<T>(
  axiosInstance: Axios,
  connector: Connector<T>,
  organizationId: string,
): Promise<Connector<T>> {

  const response = await axiosInstance.patch(
    `/api/connector/admin/${organizationId}/${connector.id}`, {
    ...connector,
  });
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to delete connector - ${response.status}`);
  }
  return response.data;
}

export async function deleteConnector<T>(
  axiosInstance: Axios,
  connectorId: number,
  organizationId: string,
): Promise<Connector<T>> {
  const response = await axiosInstance.delete(`/api/connector/admin/${organizationId}/${connectorId}`);
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to delete connector - ${response.status}`);
  }
  return response.data;
}

export async function deleteCredential<T>(
  axiosInstance: Axios,
  credentialId: number,
  organizationId: string,
) {
  const response = await axiosInstance.delete(
    `/api/connector/${organizationId}/credential/${credentialId}`,
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
  organizationId: string,
) {
  const response = await axiosInstance.put(
    `/api/connector/${organizationId}/${connectorId}/credential/${credentialId}`
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
  organizationId: string,
) {
  const response = await axiosInstance.delete(
    `/api/connector/${organizationId}/${connectorId}/credential/${credentialId}`,
  );
  if (response.status < 200 || response.status >= 300) {
    throw new Error(
      `Failed to unlink connector from credential - ${response.status}`
    );
  }
  return response.data;
}

