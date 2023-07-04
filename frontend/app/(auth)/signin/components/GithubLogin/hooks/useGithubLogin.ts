import { useSupabase } from "@/lib/context/authProvider";
import { useToast } from "@/lib/hooks/useToast";
import { useState } from "react";

export const useGithubLogin = () => {
  const { supabase } = useSupabase();

  const { publish } = useToast();
  const [isPending, setIsPending] = useState(false);
  const signInWithGithub = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "github",
      options: {
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
    setIsPending(false);
    if (error) {
      publish({
        variant: "danger",
        text: "An error occurred ",
      });
    }
  };

  return {
    signInWithGithub,
    isPending,
  };
};