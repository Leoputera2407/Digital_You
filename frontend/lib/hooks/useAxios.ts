import { useSupabase } from "@/lib/context/authProvider";
import axios from "axios";

const axiosInstance = axios.create();

export const useAxios = () => {
  const { session } = useSupabase();
  axiosInstance.interceptors.request.clear();
  axiosInstance.interceptors.request.use(
    async (config) => {
      config.headers["Authorization"] = "Bearer " + session?.access_token;
      config.headers["ngrok-skip-browser-warning"] = "true"; 
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