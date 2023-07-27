import { buildBackendHTTPUrl, getDomain } from "@/lib/redirect";
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import axios from "axios";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export const GET = async (request: NextRequest) => {
  // Use the supabase client for route handlers
  const supabase = createRouteHandlerClient({cookies});
  const { data, error } = await supabase.auth.getSession();
  
  const axiosInstance = axios.create({
    headers: {
      "Authorization": `Bearer ${data?.session?.access_token}`, 
      "Cookie": cookies().toString(),
    },
  });

  let response = null;
  const url = new URL(buildBackendHTTPUrl("/connector/google-drive/callback"));
  url.search = request.nextUrl.search;
  // This have to be withCredentials as we're making cross-origin cookies
  response = await axiosInstance.get(
    url.toString(),
    {
      withCredentials: true,
    }
  );
  
  if (response.status < 200 || response.status >= 300) {
    return NextResponse.redirect(new URL("/error", getDomain(request)));
  }
  
  const redirectResponse = NextResponse.redirect(new URL("/settings/admin/connectors", getDomain(request)));
  return redirectResponse
};
