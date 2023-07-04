import { Axios } from 'axios';

export const fetcher = async (url: string, axiosInstance: Axios) => {
  try {
    const response = await axiosInstance.get(url);
    return response.data;
  } catch (error) {
    throw new Error('An error occurred while fetching the data.');
  }
};