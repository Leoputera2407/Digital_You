import { Credential } from "@/lib/types";
import type { Axios, AxiosResponse } from "axios";

interface SetupNotionArgs {
  axiosInstance: Axios;
  userId: string;
  isPublic: boolean;
}

export const setupNotionOAuth = async ({
    axiosInstance,
    userId,
    isPublic,
  }: SetupNotionArgs): Promise<[string | null, string]> => {
    let credentialCreationResponse: AxiosResponse<Credential<{}>>;
    let authorizationUrlResponse: AxiosResponse<{auth_url: string}>;
  
    try {
      credentialCreationResponse = await axiosInstance.post(`/api/connector/credential?supabase_user_id=${userId}`, {
        public_doc: isPublic,
        credential_json: {},
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const { data: credential } = credentialCreationResponse;
      authorizationUrlResponse = await axiosInstance.get(`/api/connector/notion/authorize/${credential.id}`);
      const { data: authorizationUrlJson } = authorizationUrlResponse;
      return [authorizationUrlJson.auth_url, ""];
    } catch (error: any) {
        const status = error.response?.status || 500;
        return [null, `Failed to create credential - ${status}`];
    }
  };