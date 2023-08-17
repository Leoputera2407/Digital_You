"use client";
import AuthLogo from "@/components/ui/auth-logo";
import { useSupabase } from "@/lib/context/authProvider";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import {
  OrganizationDataResponse,
  UserRole,
  VerifyOrgResponse,
} from "@/lib/types";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import useSWR from "swr";

const PostSignInOrganizationCheck = ({ children }: { children: ReactNode}) => {
  const { session } = useSupabase();
  const { axiosInstance } = useAxios();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [hasOrganization, setHasOrganization] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  
  const excludedRoutesFromEnv = process.env.NEXT_PUBLIC_EXCLUDED_PATHS_POSTSIGNIN_CHECK 
    ? process.env.NEXT_PUBLIC_EXCLUDED_PATHS_POSTSIGNIN_CHECK.split(',').map(route => route.trim()) 
    : [];
  const excludedRoutes = [...excludedRoutesFromEnv];
  
  if (excludedRoutes.includes(pathname)) {
    return <>{children}</>;
  }
  
  const { data, error, isValidating } = useSWR<OrganizationDataResponse>(
    session && !hasOrganization ? "/api/organization//verify-org-exists-by-domain" : null, 
    (url) => fetcher(url, axiosInstance),
  );

  function checkAdminAndRedirect(role: UserRole | undefined, path: string): string {
    if (path.startsWith('/settings/admin/') && role !== UserRole.ADMIN) {
      return '/settings';
    }
    return path;
  }
  
  const verifyUserInOrg = (organizationId: string) => {
    axiosInstance.get<VerifyOrgResponse>(`/api/organization/${organizationId}/verify-user-in-org`)
      .then((response) => {
        if (response.data.success) {
          setHasOrganization(true);
          // This is to deal with cases where there are re-direction
          const searchParamsString = searchParams.toString();
          let fullPath = searchParamsString ? `${pathname}?${searchParamsString}` : pathname;
          fullPath = checkAdminAndRedirect(response.data.data?.role, fullPath);

          router.push(fullPath)
        } else {
          router.push("/log-in/join-organization");
        }
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error verifying organization membership:", error);
        setLoading(false);
        router.push("/error");
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