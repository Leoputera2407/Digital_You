import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";


function startsWithExcludedPath(pathname: string): boolean {
  const excludedPaths = [
    "/settings/connectors/google-drive/auth/callback", 
    "/settings/connectors/notion/auth/callback"
  ];
  return excludedPaths.some(excludedPath => pathname.startsWith(excludedPath));
}

export const middleware = async (req: NextRequest): Promise<NextResponse> => {
  const res = NextResponse.next();
  if (startsWithExcludedPath(req.nextUrl.pathname)) {
    return res;
  }
  const supabase = createMiddlewareClient({ req, res });
  const {
    data: {session},
  }= await supabase.auth.getSession();
  if (session && (req.nextUrl.pathname === "/" || req.nextUrl.toString() === "/?"+req.nextUrl.search)) {
    console.log("went here")
    //const redirectUrl = req.nextUrl.clone(); 
    //redirectUrl.pathname = "/settings";
    const redirectUrl = new URL('/settings', process.env.NEXT_PUBLIC_WEB_DOMAIN || 'http://localhost:3000');
    redirectUrl.search = req.nextUrl.search;
    return NextResponse.redirect(redirectUrl);
  } 
  return res;
};