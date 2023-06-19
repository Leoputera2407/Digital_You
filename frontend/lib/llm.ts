import { APIKeyJson, BaseModelJson } from "@/lib/types";
import type { Axios } from "axios";

export async function getModelConfig(axiosInstance: Axios, userId: string) {
  const response = await axiosInstance.get<BaseModelJson>(`/api/model/model-config/${userId}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data;
}

export async function upsertModelConfig(axiosInstance: Axios, userId: string, modelConfig: BaseModelJson) {
  const response = await axiosInstance.post(`/api/model/model-config/${userId}`, modelConfig, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data;
}

export async function getModelAPIKey(axiosInstance: Axios, userId?: string, keyType?: string) {

  let url = `/api/model/api-key/${userId}`;
  if (keyType) {
    url += `?key_type=${keyType}`;
  }
  const response = await axiosInstance.get<APIKeyJson[]>(url, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data;
}

export async function upsertModelAPIKey(axiosInstance: Axios, userId: string, apiKey: APIKeyJson) {
  const response = await axiosInstance.post(`/api/model/api-key/${userId}`, apiKey, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data;
}

export async function validateModelAPIKey(axiosInstance: Axios, apiKey: APIKeyJson) {
  const response = await axiosInstance.post(`/api/model/api-key/validate`, apiKey, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return response.data;
}