import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";


function startsWithExcludedPath(pathname: string): boolean {
  const excludedPaths = [
    "/_next",
    "/api/auth",
    "/settings/admin/connectors/google-drive/auth/callback", 
    "/settings/admin/connectors/notion/auth/callback",
    "/settings/admin/connectors/linear/auth/callback",
    "/privacy",
    "/terms"

  ];
  return excludedPaths.some(excludedPath => pathname.startsWith(excludedPath));
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

  // If there is a session, redirect the user to the settings page
  if (session && (req.nextUrl.pathname === '/' || req.nextUrl.pathname === '')) {
    const redirectUrl = new URL('/settings', process.env.NEXT_PUBLIC_WEB_DOMAIN || 'http://localhost:3000')
    redirectUrl.search = req.nextUrl.search
    return NextResponse.redirect(redirectUrl)
  }

  // If there is no session and the user is not on the home page, redirect them to the home page
  if (!session && req.nextUrl.pathname !== '/' && req.nextUrl.pathname !== '') {
    const redirectUrl = new URL('/', process.env.NEXT_PUBLIC_WEB_DOMAIN || 'http://localhost:3000')
    return NextResponse.redirect(redirectUrl)
  }

  return res
}