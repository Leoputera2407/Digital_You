"use client"
import { useSupabase } from '@/lib/context/authProvider'
import { redirect, useSearchParams } from 'next/navigation'
import AuthLogo from '../auth-logo'
import SignUpForm from './signup-form'


export default function SignUp() {
  const { supabase, session } = useSupabase();
  const searchParams = useSearchParams();

  if (session) {
    const slackUserId: string = searchParams.get('slack_user_id') || '';
    const teamId: string = searchParams.get('team_id') || '';
    let redirectUrl: string | null = searchParams.get('redirect_url') || null;
    redirectUrl = redirectUrl == null ? '/settings' : `${redirectUrl}?slack_user_id=${encodeURIComponent(slackUserId)}&team_id=${encodeURIComponent(teamId)}`;
    redirect(redirectUrl);
  }

  return (
  <>
    { /* Page header */}
    <div className="max-w-3xl mx-auto text-center pb-12">
      { /* Logo */}
      <AuthLogo />
      { /* Page title */}
      <h1 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60">
        Sign up to Prosona
      </h1>
    </div>

    <SignUpForm supabase={supabase}/>
  </> 
  )
}
