"use client"
import { useSupabase } from '@/lib/context/authProvider'
import { useToast } from "@/lib/hooks/useToast"
import { useState } from 'react'
import AuthButton from './AuthButton'
import { GoogleFCIcon } from './Icon'
import Logo from './logo'


export default function Header() {
  const { supabase } = useSupabase();
  const { publish } = useToast();
  const [isPending, setIsPending] = useState(false);

  
  // Function to handle sign in
  const handleSignIn = async () => {
    setIsPending(true);
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        queryParams: {
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    });
  
    if (error) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } 
    setIsPending(false);
  };

  return (
    <header className="absolute w-full z-30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16 md:h-20">

          { /* Site branding */}
          <div className="shrink-0 mr-4">
            <Logo />
          </div>

          { /* Desktop navigation */}
          <nav className="flex grow">

            { /* Desktop sign in links */}
            <ul className="flex grow justify-end flex-wrap items-center">
              <li className="ml-6">
                <AuthButton 
                  onClick={handleSignIn}
                  className="btn-sm text-slate-300 hover:text-white transition duration-150 ease-in-out w-full group [background:linear-gradient(theme(colors.slate.900),_theme(colors.slate.900))_padding-box,_conic-gradient(theme(colors.slate.400),_theme(colors.slate.700)_25%,_theme(colors.slate.700)_75%,_theme(colors.slate.400)_100%)_border-box] relative before:absolute before:inset-0 before:bg-slate-800/30 before:rounded-full before:pointer-events-none"
                  isLoading={isPending}>
                  <span className="relative inline-flex items-center">
                    <GoogleFCIcon size="20" className="mr-2" />  
                      Sign in with Google 
                    <span className="tracking-normal text-purple-500 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">-&gt;</span>
                  </span>
                </AuthButton>
              </li>
            </ul>

          </nav>

        </div>
      </div>
    </header>
  )
}
