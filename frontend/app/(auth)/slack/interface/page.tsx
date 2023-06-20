"use client"
import { useSupabase } from '@/lib/auth/authProvider';
import axios from 'axios';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';

export default function AuthSlack() {
  const { session } = useSupabase();
  const router = useRouter();
  const searchParams = useSearchParams()
 
  const slack_user_id = searchParams.get('slack_user_id') || '';
  const team_id = searchParams.get('team_id') || '';

  useEffect(() => {
    async function authenticate() {
      if (session) {
        const supabase_user_id = session.user.id;
        const redirectUri = `${process.env.NEXT_PUBLIC_BACKEND_URL}/slack/server_signup?slack_user_id=${encodeURIComponent(slack_user_id)}&team_id=${encodeURIComponent(team_id)}&supabase_user_id=${encodeURIComponent(supabase_user_id)}`;

        const response = await axios.get(redirectUri, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        });

        if (response.status === 201) {
          router.push('https://slack.com/');
        } else {
          console.error(response);
        }
      } else {
        router.push(`/signin?slack_user_id=${encodeURIComponent(slack_user_id)}&team_id=${encodeURIComponent(team_id)}&redirect=${encodeURIComponent(`${process.env.NEXT_PUBLIC_WEB_DOMAIN}/interface/slack`)}`);
      }
    }

    authenticate();
  }, [session, slack_user_id, team_id, router]);

  return null;
}