"use client";
import AuthLogo from "@/components/ui/auth-logo";
import { useSupabase } from "@/lib/context/authProvider";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import { OrganizationDataResponse } from "@/lib/types";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import useSWR from "swr";

const PostSignInOrganizationCheck = ({ children }: { children: ReactNode}) => {
  const { session } = useSupabase();
  const { axiosInstance } = useAxios();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const maxRetries = 3;

  const [hasOrganization, setHasOrganization] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const { data, error, isValidating } = useSWR<OrganizationDataResponse>(
    session && !hasOrganization ? "/api/organization//verify-org-exists-by-domain" : null, 
    (url) => fetcher(url, axiosInstance),
  );

  const verifyUserInOrg = (organizationId: string, attempt = 0) => {
    axiosInstance.get(`/api/organization/${organizationId}/verify-user-in-org`)
      .then((response) => {
        if (response.data.success) {
          setHasOrganization(true);
          const fullPath = `${pathname}?${searchParams.toString()}`;
          router.push(fullPath)
        } else {
          router.push("/log-in/join-organization");
        }
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error verifying organization membership: ", error);
        if (attempt < maxRetries) {
          setTimeout(() => {
            verifyUserInOrg(organizationId, attempt + 1);
          }, 3000);
        } else {
          router.push("/error");
          setLoading(false);
        }
      }); 
    }    
  useEffect(() => {
    if (data?.success) {
      const organizationId = data?.data!.id;
      verifyUserInOrg(organizationId);
    } else if (data && !data.success) {
      router.push("/log-in/create-organization");
      setLoading(false);
    }
  }, [data, router]);

  const excludedRoutes = ['/', '/privacy', '/terms'];
  if (excludedRoutes.includes(pathname)) {
    return <>{children}</>;
  }

  if (loading || isValidating) {
    return (
      <div className="max-w-3xl mx-auto text-center pb-12">
        <AuthLogo />
        <h1 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60">
          Loading...
        </h1>
      </div>
    )
  }

  return <>{children}</>;
};

export default PostSignInOrganizationCheck;