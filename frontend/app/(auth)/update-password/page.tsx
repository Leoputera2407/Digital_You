"use client"
import AuthButton from "@/components/ui/AuthButton";
import { useSupabase } from "@/lib/auth/authProvider";
import { useToast } from "@/lib/hooks/useToast";
import { useRouter } from "next/navigation";
import { useState } from "react";
import AuthLogo from "../auth-logo";

export default function ResetPassword() {
  const { supabase, session } = useSupabase();
  const router = useRouter();
  const [newPassword, setPassword] = useState("");
  const [isPending, setIsPending] = useState(false);
  const { publish } = useToast();

  const handlePasswordReset = async () => {
    setIsPending(true);
    const { error } = await supabase.auth.updateUser({
      password: newPassword,
    });

    if (error) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } else {
      router.refresh();
      publish({
        variant: "success",
        text: "Successfully changed password!",
      });
    }
    setIsPending(false);
  };

  if (session?.user !== undefined) {
    redirect("/upload");
  }

  return (
    <>
      {/* Page header */}
      <div className="max-w-3xl mx-auto text-center pb-12">
        {/* Logo */}
        <AuthLogo />
        {/* Page title */}
        <h1 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60">
          Reset your password
        </h1>
      </div>

      {/* Form */}
      <div className="max-w-sm mx-auto">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handlePasswordReset();
          }}
        >
          <div className="space-y-4">
            <div>
              <label
                className="block text-sm text-slate-300 font-medium mb-1"
                htmlFor="email"
              >
                Email
              </label>
              <input
                id="email"
                className="form-input w-full"
                type="email"
                required
              />
            </div>
          </div>
          <div className="mt-6">
            <AuthButton
              className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
              isLoading={isPending}
            >
              Reset Password
              <span className="tracking-normal text-purple-300 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">
                -&gt;
              </span>
            </AuthButton>
          </div>
        </form>
      </div>
    </>
  );
}
