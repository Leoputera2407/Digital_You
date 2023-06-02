export const metadata = {
  title: 'Sign In - Stellar',
  description: 'Page description',
}

import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import AuthLogo from '../auth-logo'
import SignInForm from './signin-form'

import type { Database } from '@/lib/database.types'

export default async function SignIn({
  searchParams,
}: {
  searchParams: { [key: string]: string | null};
}) {
  const supabase = createServerComponentClient<Database>({ cookies })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (session) {
    const slack_user_id = searchParams?.slack_user_id || '';
    const team_id = searchParams?.team_id || '';
    let redirectUrl: string | null = searchParams['redirect'];
    redirectUrl = redirectUrl == null ? '/settings' : `${redirectUrl}?slack_user_id=${encodeURIComponent(slack_user_id)}&team_id=${encodeURIComponent(team_id)}`;
    redirect(redirectUrl);
  }

  return (
  <>
    { /* Page header */}
    <div className="max-w-3xl mx-auto text-center pb-12">
      { /* Logo */}
      <AuthLogo />
      { /* Page title */}
      <h1 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60">Sign in to your account</h1>
    </div>

    <SignInForm />
  </>
  )
}