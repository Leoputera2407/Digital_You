import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export const middleware = async (req: NextRequest): Promise<NextResponse> => {
  const res = NextResponse.next();
  const supabase = createMiddlewareClient({ req, res });
  const {
    data: {session},
  }= await supabase.auth.getSession();

  if (session && req.nextUrl.pathname === "/") {
    const redirectUrl = req.nextUrl.clone();
    redirectUrl.pathname = "/settings";
    return NextResponse.redirect(redirectUrl);
  }

  return res;
};