import { createServerComponentClient } from '@supabase/auth-helpers-nextjs';
import axios from "axios";
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';


import type { Database } from '@/lib/database.types';

export default async function authSlack({
  searchParams,
} : {
  searchParams: { [key: string]: string | undefined };
}) {
  const supabase = createServerComponentClient<Database>({
    cookies,
  })

  const { data: { session } } = await supabase.auth.getSession();
  const slack_user_id = searchParams?.slack_user_id || '';
  const team_id = searchParams?.team_id || '';

  if (session) {
    // TODO: Check if already signup, if so, don't redirect 

    const supabase_user_id = session.user.id;

    const redirectUri = `${BACKEND_URL}/slack/server_signup?slack_user_id=${encodeURIComponent(slack_user_id)}&team_id=${encodeURIComponent(team_id)}&supabase_user_id=${encodeURIComponent(supabase_user_id)}`;


    const response = await axios.get(
      redirectUri,
      {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      }
    );

    if (response.status === 201 ) {
      // TODO: Redirect to Slack App's page after successful authentication
      redirect('https://slack.com/');
    } else {
      console.error(response);
    }
  } else {
    // cookie is preserved through the same domain/site
    redirect(`/signin?slack_user_id=${encodeURIComponent(slack_user_id)}&team_id=${encodeURIComponent(team_id)}&redirect=${encodeURIComponent(`${process.env.WEB_DOMAIN}/interface/slack`)}`);
  }
}

