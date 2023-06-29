import { useSupabase } from "@/lib/auth/authProvider";
import axios from "axios";

const axiosInstance = axios.create();

export const useAxios = () => {
  const { session } = useSupabase();
  axiosInstance.interceptors.request.clear();
  axiosInstance.interceptors.request.use(
    async (config) => {
      config.headers["Authorization"] = "Bearer " + session?.access_token;
      return config;
    },
    (error) => {
      console.error({ error });
      void Promise.reject(error);
    }
  );

  return {
    axiosInstance,
  };
};