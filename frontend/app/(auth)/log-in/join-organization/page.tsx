"use client";
import Authbutton from '@/components/ui/authButton';
import { useAxios } from '@/lib/hooks/useAxios';
import { useToast } from '@/lib/hooks/useToast';
import { OrganizationData, StatusResponse, WhitelistDataResponse } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function WhitelistedOrganizations() {
  const [organizations, setOrganizations] = useState<OrganizationData[]>([]);
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const router = useRouter();
  
  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const response = await axiosInstance.get<WhitelistDataResponse>('/api/organization/whitelisted-orgs');
        setOrganizations(response.data.data);
      } catch (err) {
        publish({
          variant: "danger",
          text: "An error occurred while fetching the organizations",
        });
      }
    }
    fetchOrgs();
  }, []);

  const joinOrganization = async (orgId: string) => {
    try {
      const response = await axiosInstance.post<StatusResponse>(`/api/organization/${orgId}/join-org`);
      if (response.data.success) {
        // Publish success toast
        publish({
          variant: "success",
          text: "Successfully joined organization",
        });
        router.push("/settings");
      } else {
        publish({
          variant: "danger",
          text: response.data.message,
        });
      }


    } catch (error) {
      publish({
        variant: "danger",
        text: "An error occurred while joining the organization",
      });
    }
  };

  return (
    <div className="max-w-sm mx-auto">
      {organizations.length === 0 ? (
        <div>Loading...</div>
      ) : (
        organizations.map((org) => (
          <div
            key={org.id}
            className="flex justify-between items-center bg-slate-900 rounded-[inherit] z-20 overflow-hidden p-3 rounded-lg shadow my-2 border border-gray-100 border-opacity-20"
          >
            <div>
              <p className="font-semibold text-slate-400 text-white">
                {org.name}
              </p>
            </div>
            <div className="space-x-2">
              <Authbutton
                onClick={() => joinOrganization(org.id)}
                className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow text-white"
              >
                Join
              </Authbutton>
            </div>
          </div>
        ))
      )}
    </div>
  );
}