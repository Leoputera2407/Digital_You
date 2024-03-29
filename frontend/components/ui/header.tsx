"use client";
import { useSupabase } from "@/lib/context/authProvider";
import { useToast } from "@/lib/hooks/useToast";
import { constructURL } from '@/lib/redirect';
import { useEffect, useState } from "react";
import AuthButton from "./authButton";
import { GoogleFCIcon } from "./icon";
import Logo from "./logo";
import SignedInUser from "./signedInUser";


export default function Header() {
  const { session, supabase } = useSupabase();
  const { publish } = useToast();
  const [isPending, setIsPending] = useState(false);
  const isLive = process.env.NEXT_PUBLIC_IS_LIVE === "true";
  const [isDesktopOrLaptop, setIsDesktopOrLaptop] = useState(true);  // default state
  const reDirectURLAfterAuth = constructURL(process.env.NEXT_PUBLIC_WEB_DOMAIN || '', '/settings/admin/connectors');
  
  async function Refresh() {
    // remove query parameters from URL
    const location = window.location;
    const cleanUrl = `${location.protocol}//${location.host}${location.pathname}`;
    window.history.pushState({}, "", cleanUrl);
  }
  useEffect(() => {
    // Update state based on actual window width once component mounts and we have access to window object
    setIsDesktopOrLaptop(window.innerWidth >= 1224);
    const handleResize = () => {
      setIsDesktopOrLaptop(window.innerWidth >= 1224);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);  // cleanup event listener on unmount
  }, []);
  
  
  useEffect(() => {
    let url = new URL(window.location.href);
    let searchParams = new URLSearchParams(url.search);
    let error = searchParams.get("error");
    let errorDescription = searchParams.get("error_description");

    if (
      error === "server_error" &&
      errorDescription === "Database error saving new user"
    ) {
      publish({
        variant: "danger",
        text: "Error: Account does not exist. Please sign up for the beta waitlist",
      });
      Refresh();
    }
  }, []);

  // Function to handle sign in
  const handleSignIn = async () => {
    setIsPending(true);
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
       redirectTo: reDirectURLAfterAuth
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
          {/* Site branding */}
          <div className="shrink-0 mr-4">
            <Logo />
          </div>

          {/* Desktop navigation */}
          <nav className="flex-grow">
            {/* Desktop sign in links */}
            <ul className="flex justify-end items-center">
              {!session && (
                <li>
                  <a
                    className="btn-sm text-slate-900 bg-gradient-to-r from-white/80 via-white to-white/80 hover:bg-white transition duration-150 ease-in-out group"
                    href="https://9a04i53lzc4.typeform.com/to/E0H4xTzS"
                  >
                      {isDesktopOrLaptop ? "Beta Waitlist" : "Beta"}{" "}
                    <span className="tracking-normal text-purple-500 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">
                      -&gt;
                    </span>
                  </a>
                </li>
              )}
              {isLive &&
                (session ? (
                  <SignedInUser />
                ) : (
                  <li className="ml-6">
                    <AuthButton
                      onClick={handleSignIn}
                      className="btn-sm text-slate-300 hover:text-white transition duration-150 ease-in-out w-full group [background:linear-gradient(theme(colors.slate.900),_theme(colors.slate.900))_padding-box,_conic-gradient(theme(colors.slate.400),_theme(colors.slate.700)_25%,_theme(colors.slate.700)_75%,_theme(colors.slate.400)_100%)_border-box] relative before:absolute before:inset-0 before:bg-slate-800/30 before:rounded-full before:pointer-events-none"
                      isLoading={isPending}
                    >
                      <span className="relative inline-flex items-center">
                        <GoogleFCIcon size="20" className="mr-2" />
                        {isDesktopOrLaptop ? "Sign in with Google" : "Sign in"}{" "}
                        <span className="tracking-normal text-purple-500 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">
                          -&gt;
                        </span>
                      </span>
                    </AuthButton>
                  </li>
                ))}
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
}
