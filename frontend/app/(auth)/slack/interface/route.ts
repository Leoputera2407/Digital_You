import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import axios from "axios";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import type { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const slack_user_id = requestUrl.searchParams.get("slack_user_id") || "";
  const team_id = requestUrl.searchParams.get("team_id") || "";

  const supabase = createRouteHandlerClient<any>({ cookies });
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session) {
    // TODO: Check if already signup, if so, don't redirect

    const supabase_user_id = session.user.id;
    const redirectUri = `${
      process.env.BACKEND_URL
    }/slack/server_signup?slack_user_id=${encodeURIComponent(
      slack_user_id
    )}&team_id=${encodeURIComponent(
      team_id
    )}&supabase_user_id=${encodeURIComponent(supabase_user_id)}`;

    const response = await axios.get(redirectUri, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });

    if (response.status === 201) {
      // TODO: Redirect to Slack App's page after successful authentication
      return NextResponse.redirect("https://slack.com/");
    } else {
      console.error(response); // Return server error response
      return NextResponse.error();
    }
  } else {
    // cookie is preserved through the same domain/site
    return NextResponse.redirect(
      `/signin?slack_user_id=${encodeURIComponent(
        slack_user_id
      )}&team_id=${encodeURIComponent(team_id)}&redirect=${encodeURIComponent(
        `${process.env.WEB_DOMAIN}/interface/slack`
      )}`
    );
  }
}
