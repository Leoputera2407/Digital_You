import { buildBackendUrl, getDomain } from "@/lib/redirect";
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import axios from "axios";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";


export const GET = async (request: NextRequest) => {
  const supabase = createRouteHandlerClient({cookies});
  const { data, error } = await supabase.auth.getSession();

  const axiosInstance = axios.create({
    headers: {
      "Authorization": `Bearer ${data?.session?.access_token}`, 
      "Cookie": cookies()
        .getAll()
        .map((cookie) => `${cookie.name}=${cookie.value}`)
        .join("; "),
    },
  });

  let response = null;
  if (process.env.NODE_ENV === "production") {
    const url = new URL(buildBackendUrl("/connector/notion/callback"));
    url.search = request.nextUrl.search;
    url.searchParams.append('supabase_user_id', data?.session?.user?.id || '');
    // Make the request
    response = await axiosInstance.get(url.toString());
  } else {
    const url = new URL(buildBackendUrl("/connector/notion-non-prod/callback"));
    url.search = request.nextUrl.search;
    url.searchParams.append('supabase_user_id', data?.session?.user?.id || '');
    // Make the request
    response = await axiosInstance.get(url.toString());
  }

  if (response.status < 200 || response.status >= 300) {
    console.log(
      "Error in Notion callback:",
      response.data.message
    );
    return NextResponse.redirect(new URL("/error", getDomain(request)));
  }

  return NextResponse.redirect(new URL("/settings/connectors", getDomain(request)));
};
