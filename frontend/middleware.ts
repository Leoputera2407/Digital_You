import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";


function startsWithExcludedPath(pathname: string): boolean {
  // Permanent excluded paths
  const permanentExcludedPaths = [
    "/_next",
    "/api/auth"
  ];

  const excludedPathsEnv = process.env.NEXT_PUBLIC_EXCLUDED_PATHS_SUPABASE_MIDDLEWARE || "";
  const envExcludedPaths = excludedPathsEnv.split(',').map(path => path.trim());
  
  const allExcludedPaths = [...permanentExcludedPaths, ...envExcludedPaths];

  return allExcludedPaths.some(excludedPath => pathname.startsWith(excludedPath));
}

function hasCodeQueryParam(nextUrl: URL): boolean {
  return Boolean(nextUrl.searchParams.get('code'));
}

export const middleware = async (req: NextRequest): Promise<NextResponse> => {
  const res = NextResponse.next()

  if (startsWithExcludedPath(req.nextUrl.pathname)) {
    return res
  }

  const supabase = createMiddlewareClient({ req, res })

  // Check if we have a session
  const { data: {session} } = await supabase.auth.getSession()

  // If user is in the accept invitation, don't redirect
  if (req.nextUrl.pathname === '/accept-invitation') {
    return res
  }

  // If there is a session, redirect the user to the /settings/admin/connectors page
  if (session && (req.nextUrl.pathname === '/' || req.nextUrl.pathname === '')) {
    const redirectUrl = new URL('/settings/admin/connectors', process.env.NEXT_PUBLIC_WEB_DOMAIN || 'http://localhost:3000')
    redirectUrl.search = req.nextUrl.search
    return NextResponse.redirect(redirectUrl)
  }

  // If there is no session and the user is not on the home page, redirect them to the home page
  if (
    !session 
    && req.nextUrl.pathname !== '/' 
    && req.nextUrl.pathname !== ''
    && !(
      req.nextUrl.pathname === '/settings/admin/connectors' && hasCodeQueryParam(req.nextUrl)
    )
  ) {
    const redirectUrl = new URL('/', process.env.NEXT_PUBLIC_WEB_DOMAIN || 'http://localhost:3000')
    return NextResponse.redirect(redirectUrl)
  }

  if (session && req.nextUrl.pathname === '/settings/admin/connectors' && hasCodeQueryParam(req.nextUrl)) {
    const redirectUrl = new URL('/settings/admin/connectors', process.env.NEXT_PUBLIC_WEB_DOMAIN || 'http://localhost:3000');
    redirectUrl.searchParams.delete('code');
    return NextResponse.redirect(redirectUrl);
  }

  return res
}