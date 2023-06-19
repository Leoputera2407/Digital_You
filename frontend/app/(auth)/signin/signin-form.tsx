"use client";

import AuthButton from "@/components/ui/AuthButton";
import Field from "@/components/ui/Field";
import { useToast } from "@/lib/hooks/useToast";
import type { SupabaseClient } from "@supabase/auth-helpers-nextjs";
import Link from "next/link";
import { useState } from "react";
import { GithubLoginButton } from "./components/GithubLogin";
import { GoogleLoginButton } from "./components/GoogleLogin";

interface SignInFormProps {
  supabase: SupabaseClient;
}

const SignInForm: React.FC<SignInFormProps> = ({ supabase }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isPending, setIsPending] = useState(false);
  const { publish } = useToast();

  const handleSignIn = async () => {
    setIsPending(true);
    const { data , error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } else {
      console.log("Successfully logged in with credentials: ", data);
      publish({
        variant: "success",
        text: "Successfully logged in",
      });
    }
    setIsPending(false);
  };

  return (
    <>
      <div className="max-w-sm mx-auto">
        <form onSubmit={(e) => {
              e.preventDefault();
              handleSignIn();
          }}
        >
          <div className="space-y-4">
            <Field
              id="email"
              className="form-input w-full"
              type="email"
              required
              name="email"
              placeholder="Email"
              onChange={(e) => setEmail(e.target.value)}
              value={email}
            />
            <Field
              id="password"
              className="form-input w-full"
              type="password"
              autoComplete="on"
              required
              name="password"
              placeholder="Password"
              onChange={(e) => setPassword(e.target.value)}
              value={password}
            />
          </div>
          <div className="mt-6">
            <AuthButton
              isLoading={isPending}
              className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
            >
              Sign In{" "}
              <span className="tracking-normal text-purple-300 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">
                -&gt;
              </span>
            </AuthButton>
          </div>
        </form>

        <div className="text-center mt-4">
          <div className="text-sm text-slate-400">
            Don't have an account?{" "}
            <Link
              className="font-medium text-purple-500 hover:text-purple-400 transition duration-150 ease-in-out"
              href="/signup"
            >
              Sign up
            </Link>
          </div>
        </div>

        {/* Divider */}
        <div className="flex items-center my-6">
          <div
            className="border-t border-slate-800 grow mr-3"
            aria-hidden="true"
          />
          <div className="text-sm text-slate-500 italic">or</div>
          <div
            className="border-t border-slate-800 grow ml-3"
            aria-hidden="true"
          />
        </div>

        {/* Social login */}
        <div className="flex space-x-3">
          <GithubLoginButton />
          <GoogleLoginButton />
        </div>
      </div>
    </>
  );
}

export default SignInForm;