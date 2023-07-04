"use client";

import type { SupabaseClient, User } from "@supabase/auth-helpers-nextjs";
import {
  Session,
  createPagesBrowserClient,
} from "@supabase/auth-helpers-nextjs";
import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

type MaybeSession = Session | null;
type MaybeUser = User | null;

type SupabaseContext = {
  supabase: SupabaseClient;
  session: MaybeSession;
  user: MaybeUser;
};

const AuthContext = createContext<SupabaseContext | undefined>(undefined);

const AuthProvider =({
  session: initialSession,
  children,
}: {
  session: MaybeSession;
  children: React.ReactNode;
}): JSX.Element => {
  const [supabase] = useState(() => createPagesBrowserClient())
  const [session, setSession] = useState<MaybeSession>(initialSession);
  const [user, setUser] = useState<MaybeUser>(initialSession?.user ?? null);
  const router = useRouter();

  useEffect(() => {
    const {
      data: { subscription},
    } = supabase.auth.onAuthStateChange((event, currentSession) => {
      if (currentSession?.access_token !== session?.access_token) {
        router.refresh();
      }
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
    });

    return () => {
      subscription?.unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo(() => {
    return { 
      supabase, 
      session, 
      user, 
    };
  }, [supabase, session, user]);
  
  return (
    <AuthContext.Provider value={value}>
      <>{children}</>
    </AuthContext.Provider>
  
  );
};


export const useSupabase = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useSupabase must be used within a AuthContextProvider.");
  }
  return context;
};

export default AuthProvider;