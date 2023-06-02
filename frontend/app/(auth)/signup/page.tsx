export const metadata = {
  title: 'Sign Up - Stellar',
  description: 'Page description',
}

import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import AuthLogo from '../auth-logo'
import SignUpForm from './signup-form'

import type { Database } from '@/lib/database.types'

export default async function SignUp() {

  const supabase = createServerComponentClient<Database>({ cookies })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (session) {
    redirect('/settings')
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
