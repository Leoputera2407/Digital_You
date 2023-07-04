import { useSupabase } from "@/lib/context/authProvider";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import { OrganizationBase, UserOrgResponse } from "@/lib/types";
import useSWR, { mutate } from "swr";


type UseAccountResponse = {
  organizations: OrganizationBase[] | undefined;
  isLoading: boolean;
  isError: boolean;
  revalidate: () => void;
};

const useAccount = (): UseAccountResponse => {
  const { session } = useSupabase();
  const { axiosInstance } = useAxios();

  const shouldFetch = session !== null; // Define when we should fetch

  const { data, error } = useSWR<UserOrgResponse>(
    shouldFetch ? `/api/account/get-user-org-and-roles` : null,
    (url) => fetcher(url, axiosInstance),
  );

  return {
    organizations: data?.organizations,
    isLoading: !error && !data,
    isError: error,
    revalidate: () => mutate('/api/get-user-org-and-roles'),
  };
};

export default useAccount;