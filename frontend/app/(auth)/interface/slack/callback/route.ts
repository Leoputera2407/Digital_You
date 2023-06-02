import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

import type { NextRequest } from 'next/server'
import type { Database } from '@/lib/database.types'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const supabase = createServerComponentClient<Database>({
    cookies,
    })

  if (code) {
    console.log('code', code)
    // Exchange code for workspace_id and slack_user_id, map to user.id
    let result;
    try {
        const redirectURI = `${process.env.WEB_DOMAIN}/interface/slack/callback`
        console.log('redirectURI', redirectURI)
        result = await fetch(`https://slack.com/api/oauth.v2.access?client_id=${process.env.SLACK_CLIENT_ID}&client_secret=${process.env.SLACK_CLIENT_SECRET}&code=${code}&redirect_uri=${encodeURIComponent(redirectURI)}`);
    } catch (error) {
        console.error('Failed to fetch from Slack API: ', error)
        return redirect('/error')
    }
    const data = await result.json();
    console.log('data', data)

    if (!data.ok) {
        console.error('Error from Slack API: ', data)
        // return redirect('/error') 
    }

    const { team: { id: workspace_id }, authed_user: { id: slack_user_id } } = data;
    const updates = { workspace_id, slack_user_id };

    // Get current session
    const { data: {session}, error } = await supabase.auth.getSession();

    if (error || !session) {
      // If no session found, redirect to sign in with a callback to this page
      return redirect(`/error`)
    }

    // Update user with Slack data
    try {
        await supabase.from('users').update(updates).match({ id: session.user.id });
    } catch (error) {
        console.error('Failed to update user: ', error)
        return redirect('/error')
    }
  }

  // URL to redirect to after sign in process completes
  return NextResponse.redirect(`https://slack.com/services/${process.env.APP_ID}`);
}