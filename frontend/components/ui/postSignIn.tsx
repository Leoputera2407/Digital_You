"use client";
import { useSupabase } from "@/lib/context/authProvider";
import { fetcher } from "@/lib/fetcher";
import { OrganizationDataResponse } from "@/lib/types";
import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import useSWR from "swr";

const PostSignInOrganizationCheck = ({ children }: { children: ReactNode}) => {
  const { session } = useSupabase();
  const router = useRouter();

  const [hasOrganization, setHasOrganization] = useState<boolean>(false);

  const { data } = useSWR<OrganizationDataResponse>(() => {
    if (session && !hasOrganization) {
      return "/api/organization/verify-org-exists";
    }
    return null;
  }, fetcher);

  useEffect(() => {
    if (data?.success) {
      setHasOrganization(true);
    } else if (data && !data.success) {
      router.push("/create-organization");
    }
  }, [data, router]);

  return <>{children}</> ?? <></>;
};

export default PostSignInOrganizationCheck;