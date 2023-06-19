"use client";

import AuthButton from "@/components/ui/AuthButton";
import Field from "@/components/ui/Field";
import { useToast } from "@/lib/hooks/useToast";
import type { SupabaseClient } from "@supabase/auth-helpers-nextjs";
import Link from "next/link";
import { useState } from "react";

interface SignUpFormProps {
  supabase: SupabaseClient;
}

const SignUpForm: React.FC<SignUpFormProps> = ({ supabase }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [isPending, setIsPending] = useState(false);
  const { publish } = useToast();

  const handleSignUp = async () => {
    setIsPending(true);
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${location.origin}/auth/callback`,
        data: {
          first_name: firstName,
          last_name: lastName,
          email: email,
        },
      },
    });
    if (error) {
      console.error("Error signing up:", error.message);
      publish({
        variant: "danger",
        text: `Error signing up: ${error.message}`,
      });
    } else if (data) {
      publish({
        variant: "success",
        text: "Confirmation Email sent, please check your email",
      });
    }
    setIsPending(false);
  };
  return (
    <>
      <div className="max-w-sm mx-auto">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSignUp();
          }}
        >
          <div className="space-y-4">
            <Field
              id="first-name"
              className="form-input w-full"
              type="text"
              required
              name="first name"
              placeholder="E.g., Mark"
              onChange={(e) => setFirstName(e.target.value)}
              value={firstName}
            />
            <Field
              id="last-name"
              className="form-input w-full"
              type="text"
              required
              name="last name"
              placeholder="E.g., Rossi"
              onChange={(e) => setLastName(e.target.value)}
              value={lastName}
            />
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
            <AuthButton
              isLoading={isPending}
              className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
            >
              Sign Up{" "}
              <span className="tracking-normal text-purple-300 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">
                -&gt;
              </span>
            </AuthButton>
          </div>
        </form>

        <div className="text-center mt-4">
          <div className="text-sm text-slate-400">
            Already have an account?{" "}
            <Link
              className="font-medium text-purple-500 hover:text-purple-400 transition duration-150 ease-in-out"
              href="/signin"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};

export default SignUpForm;
