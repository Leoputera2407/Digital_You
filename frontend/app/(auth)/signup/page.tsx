export const metadata = {
  title: 'Sign Up - Stellar',
  description: 'Page description',
}

import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import AuthLogo from '../auth-logo'
import SignUpForm from './signup-form'

import type { Database } from '@/lib/database.types'

export default async function SignUp({
  searchParams,
} : {
  searchParams: { [key: string]: string | null };
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
        <h1 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60">Create your free account</h1>
      </div>

      <SignUpForm />
    </>
  )
}
