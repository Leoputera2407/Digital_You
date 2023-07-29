"use client";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormLabel,
  FormMessage,
} from "@/components/react-hook-form/form";
import AuthLogo from "@/components/ui/auth-logo";
import { useSupabase } from "@/lib/context/authProvider";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { StatusResponse } from "@/lib/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

const OrgCreationSchema = z.object({
  organizationName: z.string().min(2, {
    message: "Organization name must be at least 2 characters.",
  }),
  userList: z.string().or(z.literal("")),
});

export default function CreateOrg() {
  const { user } = useSupabase();
  const router = useRouter();
  const { publish } = useToast();
  const { axiosInstance } = useAxios();
  const [userDomain, setUserDomain] = useState<string | null>(null);

  const form = useForm<z.infer<typeof OrgCreationSchema>>({
    resolver: zodResolver(OrgCreationSchema),
  });

  useEffect(() => {
    if(user?.email) {
      const domain = user.email.split('@')[1];
      setUserDomain(domain);
    }
  }, [user]);

  async function onSubmit(data: z.infer<typeof OrgCreationSchema>) {
    const userList = data.userList ? data.userList.split(',').map((user) => user.trim()) : [];
    const isValid = userList.length ? userList.every((user) => user.endsWith(`@${userDomain}`)) : true;
  
    if (!isValid) {
      form.setError("userList", {
        type: "manual",
        message: "All emails must be from the same domain as the current user."
      });
      return;
    }
  
    const payload = {
      name: data.organizationName,
      invited_users: userList.map(email => ({ user_email: email })),
    };
  
    try {
      const response = await axiosInstance.post<StatusResponse>("/api/organization/create-org-and-add-admin", payload);
  
      if (response.data.success) {
        // Publish success toast
        publish({
          variant: "success",
          text: "Successfully created organization and added admin!",
        });
        router.push("/settings");
      } else {
        // Publish error toast
        publish({
          variant: "danger",
          text: response.data.message,
        });
      }
    } catch (error) {
      // Publish error toast
      publish({
        variant: "danger",
        text: "An error occurred while creating the organization",
      });
    }
  }

  return (
    <>
      {/* Page header */}
      <div className="max-w-3xl mx-auto text-center pb-12">
        {/* Logo */}
        <AuthLogo />
        {/* Page title */}
        <h1 className="h2 bg-clip-text text-transparent bg-gradient-to-r from-slate-200/60 via-slate-200 to-slate-200/60">
          Create your organization
        </h1>
      </div>

      {/* Form */}
      <div className="max-w-sm mx-auto">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="organizationName"
              render={({ field, fieldState: { error } }) => (
                <div>
                  <FormLabel className="block text-sm text-slate-300 font-medium mb-1">
                    Organization Name
                  </FormLabel>
                  <FormControl>
                    <input className="form-input w-full" {...field} />
                  </FormControl>
                  <FormMessage color={error && "red"}>
                    {error?.message}
                  </FormMessage>
                </div>
              )}
            />
            <FormField
              control={form.control}
              name="userList"
              render={({ field, fieldState: { error } }) => (
                <div>
                  <FormLabel className="block text-sm text-slate-300 font-medium mb-1">
                    Users to Invite
                  </FormLabel>
                  <FormControl>
                    <textarea className="form-input w-full" {...field} />
                  </FormControl>
                  <FormDescription>
                    Enter the email addresses of the users to invite, separated
                    by commas. e.g. name1@company.com, name2@company.com, ...
                  </FormDescription>
                  <FormMessage color={error && "red"}>
                    {error?.message}
                  </FormMessage>
                </div>
              )}
            />
            <div className="mt-6">
              <button className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group">
                Create Organization{" "}
                <span className="tracking-normal text-purple-300 group-hover:translate-x-0.5 transition-transform duration-150 ease-in-out ml-1">
                  -&gt;
                </span>
              </button>
            </div>
          </form>
        </Form>
      </div>
    </>
  );
}
