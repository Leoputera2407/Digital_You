export const metadata = {
  title: "Reset Password - Digital You",
  description: "Page description",
};
import AuthButton from "@/components/ui/AuthButton";
import Field from "@/components/ui/Field";
import { useSupabase } from "@/lib/context/authProvider";
import { useToast } from "@/lib/hooks/useToast";
import { useRouter } from "next/navigation";
import { useState } from "react";
import AuthLogo from "../auth-logo";

export default function ResetPassword() {
  const { supabase } = useSupabase();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [isPending, setIsPending] = useState(false);
  const { publish } = useToast();

  const handlePasswordReset = async () => {
    setIsPending(true);
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      // TODO: Set the correct page
      redirectTo: "http://localhost:3000/update-password",
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
        text: "Password reset email sent! Check your inbox.",
      });
    }
    setIsPending(false);
  };
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
