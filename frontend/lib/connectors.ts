import type { Axios } from "axios";
import {
  ConfluenceTestBase,
  Connector,
  ConnectorBase,
  Credential,
  GithubTestBase,
  LinearOrganizationSnapshot,
  NotionWorkspaceSnapshot,
} from "./types";

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

export async function createCredential<T>(
  {
    axiosInstance,
    publicDoc,
    credentialJson,
    organizationId,
  }: {
    axiosInstance: Axios;
    publicDoc: boolean;
    credentialJson: T;
    organizationId: string;
  }
): Promise<Credential<T>> {
  const response = await axiosInstance.post<Credential<T>>(
    `/api/connector/${organizationId}/credential`,
    {
      public_doc: publicDoc,
      credential_json: credentialJson,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to create credential - ${response.status}`);
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

export async function testGithubAccessToken(
  axiosInstance: Axios,
  githubTestInfo: GithubTestBase,
  organizationId: string,
): Promise<{ data: any; error: string | null }> {
  try {
    const response = await axiosInstance.post(
      `/api/connector/admin/${organizationId}/test-github`,
      {
        ...githubTestInfo,
      }
    );
    if (response.data.success === false) {
      return { data: null, error: response.data.message };
    }
    return { data: response.data, error: null };
  } catch (error: any) {
    if (error.response) {
      // The request was made and the server responded with a non-2xx status code
      return { data: null, error: `Failed to validate github access token - ${error.response.data.message}` };
    } else {
      // Something happened in setting up the request and triggered an Error
      return { data: null, error: error.message };
    }
  }
}

export async function testConfluenceAccessToken(
  axiosInstance: Axios,
  confleunceTestInfo: ConfluenceTestBase,
  organizationId: string,
): Promise<{ data: any; error: string | null }> {
  try {
    const response = await axiosInstance.post(
      `/api/connector/admin/${organizationId}/test-confluence`,
      {
        ...confleunceTestInfo,
      }
    );
    if (response.data.success === false) {
      return { data: null, error: response.data.message };
    }
    return { data: response.data, error: null };
  } catch (error: any) {
    if (error.response) {
      // The request was made and the server responded with a non-2xx status code
      return { data: null, error: `Failed to validate confluence access token - ${error.response.data.message}` };
    } else {
      // Something happened in setting up the request and triggered an Error
      return { data: null, error: error.message };
    }
  }
}


export async function fetchLinearOrgAndTeam(
  axiosInstance: Axios,
  organizationId: string,
  linearCredentialId: number,
): Promise<LinearOrganizationSnapshot> {
  const response = await axiosInstance.get<LinearOrganizationSnapshot>(
    `/api/connector/admin/${organizationId}/get-linear-org-and-team`,
    {
      params: {
        linear_credential_id: linearCredentialId
      }
    }
  );
  
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to fetch Linear organization and team - ${response.status}`);
  }

  return response.data;
}

export async function fetchNotionWorkspace(
  axiosInstance: Axios,
  organizationId: string,
  notionCredentialId: number,
): Promise<NotionWorkspaceSnapshot> {
  const response = await axiosInstance.get(
    `/api/connector/admin/${organizationId}/get-notion-workspace`,
    {
      params: {
        notion_credential_id: notionCredentialId
      }
    }
  );

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Failed to fetch Notion workspace - ${response.status}`);
  }

  return response.data;
}
