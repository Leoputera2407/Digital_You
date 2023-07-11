"use client";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/react-hook-form/form";
import Authbutton from "@/components/ui/authButton";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useOrganization } from "@/lib/context/orgProvider";
import { useOrgAdminOps } from "@/lib/hooks/useOrgAdminOps";
import { OrganizationAdminInfo } from "@/lib/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

const domainRegex = /^([a-z0-9](-*[a-z0-9])*)(\.([a-z0-9](-*[a-z0-9])*))*$/i;

const orgUpdateFormSchema = z.object({
  organizationName: z.string().min(2, {
    message: "Organization name must be at least 2 characters.",
  }),
  emailDomain: z.string().refine((domain) => domainRegex.test(domain), {
    message:
      "Invalid domain format. It should be something like 'example.com' or 'subdomain.example.com",
  }),
});

const inviteUserFormSchema = z.object({
  inviteEmail: z.string().email(),
});

function countPendingInvitationsAndMembers(
  adminOrgInfo: OrganizationAdminInfo | undefined
) {
  const numInvitations = adminOrgInfo?.pending_invitations?.length || 0;
  const numMembers = adminOrgInfo?.users?.length || 0;

  return { numInvitations, numMembers };
}

function combineMembersAndPendingInvitations(
  adminOrgInfo: OrganizationAdminInfo | undefined
) {
  const members =
    adminOrgInfo?.users?.map((user) => ({
      email: user.user_email,
      isPending: false,
    })) || [];

  const invitations =
    adminOrgInfo?.pending_invitations?.map((invitation) => ({
      email: invitation.email,
      isPending: true,
    })) || [];

  return [...members, ...invitations];
}

export default function ProfileFormPage() {
  const { currentOrganization } = useOrganization();
  const {
    adminOrgInfo,
    isAdminOrgInfoError,
    handleAddUserToOrg,
    handleRemoveUserFromOrg,
    handlePromoteUserToAdmin,
    handleUpdateAdminOrganizationInfo,
  } = useOrgAdminOps(currentOrganization?.id);

  const { numInvitations, numMembers } =
    countPendingInvitationsAndMembers(adminOrgInfo);
  const combinedUserList = combineMembersAndPendingInvitations(adminOrgInfo);
  console.log(adminOrgInfo);
  const orgForm = useForm<z.infer<typeof orgUpdateFormSchema>>({
    resolver: zodResolver(orgUpdateFormSchema),
  });

  const inviteUserForm = useForm<z.infer<typeof inviteUserFormSchema>>({
    resolver: zodResolver(inviteUserFormSchema),
  });

  useEffect(() => {
    orgForm.setValue("organizationName", adminOrgInfo?.name || "");
    orgForm.setValue(
      "emailDomain",
      adminOrgInfo?.whitelisted_email_domain || ""
    );
  }, [adminOrgInfo, orgForm]);

  async function onUpdateOrgSubmit(
    values: z.infer<typeof orgUpdateFormSchema>
  ) {
    await handleUpdateAdminOrganizationInfo(
      values.emailDomain,
      values.organizationName
    );
  }

  async function onAddUserSubmit(values: z.infer<typeof inviteUserFormSchema>) {
    inviteUserForm.setValue("inviteEmail", "");
    await handleAddUserToOrg(values.inviteEmail);
  }

  const onRevokeClick = async (email: string, isPending: boolean) => {
    await handleRemoveUserFromOrg(email, isPending);
  };

  const onPromoteClick = async (email: string) => {
    await handlePromoteUserToAdmin(email);
  };

  return (
    <>
    <Form {...orgForm}>
      <form
        onSubmit={orgForm.handleSubmit(onUpdateOrgSubmit)}
        className="space-y-4"
      >
        <div className="space-y-1">
          <h2 className="text-md font-medium text-white">Workspace Settings</h2>
          <p className="text-sm text-muted-foreground">
            A workspace lets you collaborate with your team.
          </p>
          <Separator className="my-3" />
        </div>
        <FormField
          control={orgForm.control}
          name="organizationName"
          render={({ field, fieldState: { error } }) => (
            <FormItem>
              <FormLabel className="text-white">Organization Name</FormLabel>
              <FormControl>
                <Input placeholder="Your organization name" {...field} />
              </FormControl>
              <FormDescription>The name of our organization</FormDescription>
              <FormMessage color={error && "red"}>
                {error?.message}
              </FormMessage>
            </FormItem>
          )}
        />
        <FormField
          control={orgForm.control}
          name="emailDomain"
          render={({ field, fieldState: { error } }) => (
            <FormItem>
              <FormLabel className="text-white">Whitelisted E-mail Domain</FormLabel>
              <FormControl>
                <Input
                  placeholder="Your whitelisted e-mail domain"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Allow any user with an e-mail from the specified domain to
                auto join this workspace
              </FormDescription>
              <FormMessage color={error && "red"}>
                {error?.message}
              </FormMessage>
            </FormItem>
          )}
        />
       <div className="flex justify-end">
        <Authbutton 
          type="submit" 
          className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
        >
          Update
        </Authbutton>
      </div>
      </form>
    </Form>
    < Separator />
    <Form {...inviteUserForm}>
      <form
        onSubmit={inviteUserForm.handleSubmit(onAddUserSubmit)}
        className="space-y-4"
      >
        <h2 className="text-md font-medium text-white">Workspace Members</h2>
        <p className="text-sm text-muted-foreground">
          Manage active members and invitations to your workspace.
        </p>
        <FormField
          control={inviteUserForm.control}
          name="inviteEmail"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-white">Invite by Email</FormLabel>
              <FormControl>
                <Input placeholder="Email to invite" {...field} />
              </FormControl>
              <div className="flex justify-end">
                <Authbutton 
                  type="submit" 
                  className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
                >
                  Send Invite
                </Authbutton>
              </div>
            </FormItem>
          )}
        />
      </form>
    </Form>
  
    <h3 className="my-4 text-white">
      {numInvitations} Invitations and {numMembers} Members
    </h3>
    {combinedUserList.map((member) => (
      <div
      key={member.email}
      className="flex justify-between items-center bg-slate-900 rounded-[inherit] z-20 overflow-hidden p-3 rounded-lg shadow my-2 border border-gray-100 border-opacity-20"
    >
      <div>
        <p
          className={`font-semibold text-slate-400 ${
            member.isPending ? "text-gray-400" : "text-white"
          }`}
        >
          {member.email}
          {member.isPending && (
            <span className="italic text-gray-500"> (Pending)</span>
          )}
        </p>
      </div>
      <div className="space-x-2">
        {!member.isPending && (
          <Authbutton
            onClick={() => onPromoteClick(member.email)}
            className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow text-white"
          >
            Promote to Admin
          </Authbutton>
        )}
        <Authbutton
          onClick={() => onRevokeClick(member.email, member.isPending)}
          className="text-sm bg-red-500 hover:bg-red-600 px-4 py-1 rounded shadow text-white"
        >
          Revoke
        </Authbutton>
      </div>
    </div>
    ))}
  </>
  );
}
