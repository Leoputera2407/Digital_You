import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { Analytics } from "@vercel/analytics/react";
import { Inter } from "next/font/google";
import { cookies } from "next/headers";
import "./css/style.css";

import PostSignInOrganizationCheck from "@/components/ui/postSignIn";
import AuthProvider from "@/lib/context/authProvider";
import { OrganizationProvider } from "@/lib/context/orgProvider";
import { PHProvider } from "@/lib/context/postHogProvider";
import { ToastProvider } from "../components/ui/Toast";


const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata = {
  title: "Prosona",
  description: "Empowering Knowledge Workers",
};

const RootLayout = async ({
  children,
}: {
  children: React.ReactNode;
}): Promise<JSX.Element> => {
  const supabase = createServerComponentClient({
    cookies,
  });

  const {
    data: { session },
  } = await supabase.auth.getSession();
  return (
    <html lang="en">
      <PHProvider>
        <body
          className={`${inter.variable} font-inter antialiased bg-slate-900 text-slate-100 tracking-tight`}
        >
          <AuthProvider session={session}>
            <PostSignInOrganizationCheck>
              <OrganizationProvider>
                <ToastProvider>
                  <div className="flex flex-col min-h-screen overflow-hidden">
                    {children}
                  </div>
                </ToastProvider>
              </OrganizationProvider>
            </PostSignInOrganizationCheck>
            <Analytics />
          </AuthProvider>
        </body>
      </PHProvider>
    </html>
  );
};

export default RootLayout;
