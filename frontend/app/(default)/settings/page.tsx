import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/react-hook-form/form';
import Authbutton from "@/components/ui/AuthButton";
import { Input } from "@/components/ui/Input";
import { Separator } from "@/components/ui/Separator";
import { useOrganization } from '@/lib/context/orgProvider';
import { useOrgAdminOps } from '@/lib/hooks/useOrgAdminOps';
import { OrganizationAdminInfo } from '@/lib/types';
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";

const orgUpdateFormSchema = z.object({
  organizationName: z.string().min(2, {
    message: "Organization name must be at least 2 characters.",
  }),
  emailDomain: z.string().email(),
})

const inviteUserFormSchema = z.object({
  inviteEmail: z.string().email(),
})

function countPendingInvitationsAndMembers(adminOrgInfo: OrganizationAdminInfo | undefined) {
  const numInvitations = adminOrgInfo?.pending_invitations?.length || 0;
  const numMembers = adminOrgInfo?.users?.length || 0;

  return { numInvitations, numMembers };
}

function combineMembersAndPendingInvitations(adminOrgInfo: OrganizationAdminInfo | undefined) {
  const members = adminOrgInfo?.users?.map(user => ({
    email: user.user_email,
    isPending: false,
  })) || [];

  const invitations = adminOrgInfo?.pending_invitations?.map(invitation => ({
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
  } = useOrgAdminOps(
    currentOrganization?.id
  )
  
  const { numInvitations, numMembers } = countPendingInvitationsAndMembers(adminOrgInfo);
  const combinedUserList = combineMembersAndPendingInvitations(adminOrgInfo);

  const orgForm = useForm<z.infer<typeof orgUpdateFormSchema>>({
    resolver: zodResolver(orgUpdateFormSchema),
    defaultValues: {
      organizationName: adminOrgInfo?.name || "",
      emailDomain: adminOrgInfo?.whitelisted_email_domain || "",
    },
  })

  const inviteUserForm = useForm<z.infer<typeof inviteUserFormSchema>>({
    resolver: zodResolver(inviteUserFormSchema),
    defaultValues: {
      inviteEmail: "",
    },
  })

  async function onUpdateOrgSubmit(values: z.infer<typeof orgUpdateFormSchema>) {
    await handleUpdateAdminOrganizationInfo(values.emailDomain, values.organizationName)
  }

  async function onAddUserSubmit(values: z.infer<typeof inviteUserFormSchema>) {
    await handleAddUserToOrg(values.inviteEmail);
  }

  const onRevokeClick = async (email: string, isPending: boolean) => {
    await handleRemoveUserFromOrg(email, isPending);
  }

  const onPromoteClick = async (email: string) => {
    await handlePromoteUserToAdmin(email);
  }


  return (
    <>
    <Form {...orgForm}>
      <form onSubmit={orgForm.handleSubmit(onUpdateOrgSubmit)} className="space-y-8">
        <h2 className="text-md font-medium">Workspace Settings</h2>
        <p className="text-sm text-muted-foreground">A workspace lets you collaborate with your team.</p>
        <Separator />
        <FormField
          control={orgForm.control}
          name="organizationName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Organization Name</FormLabel>
              <FormControl>
                <Input placeholder="Your organization name" {...field} />
              </FormControl>
              <FormDescription>
                The name of our organization
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={orgForm.control}
          name="emailDomain"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Whitelisted E-mail Domain</FormLabel>
              <FormControl>
                <Input placeholder="Your whitelisted e-mail domain" {...field} />
              </FormControl>
              <FormDescription>
                Allow any user with an e-mail from the specified domain to auto join this workspace
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <Authbutton type="submit">Update</Authbutton>
        </form>
</Form>
<Form {...inviteUserForm}>
  <form onSubmit={inviteUserForm.handleSubmit(onAddUserSubmit)} className="space-y-8">

        <h2 className="text-md font-medium">Workspace Members</h2>
        <p className="text-sm text-muted-foreground">Manage active members and invitations to your workspace.</p>
        <Separator />
        <FormField
          control={inviteUserForm.control}
          name="inviteEmail"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Invite by Email</FormLabel>
              <FormControl>
                <Input placeholder="Email to invite" {...field} />
              </FormControl>
              <Authbutton type="submit">Send</Authbutton>
            </FormItem>
          )}
        />
         </form>
    </Form>

      <h3 className="my-4">{numInvitations} Invitations and {numMembers} Members</h3>
      {combinedUserList.map(member => (
        <div key={member.email} className="flex justify-between items-center bg-white p-3 rounded-lg shadow my-2">
          <div>
            <p className={`font-semibold ${member.isPending ? 'text-gray-400' : 'text-black'}`}>
              {member.email}
              {member.isPending && <span className="italic text-gray-500"> (Pending)</span>}
            </p>
          </div>
          <div className="space-x-2">
            { !member.isPending &&
              <Authbutton 
                onClick={() => onPromoteClick(member.email)} 
                className="text-sm text-white bg-blue-500 hover:bg-blue-600 shadow-sm group"
              >
                Promote to Admin
              </Authbutton>
            }
            <Authbutton 
              onClick={() => onRevokeClick(member.email, member.isPending)} 
              className="text-sm text-white bg-red-500 hover:bg-red-600 shadow-sm group"
            >
              Revoke
            </Authbutton>
          </div>
        </div>
      ))}
  </>
  )  
}