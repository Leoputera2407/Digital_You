"use client";
import AuthButton from "@/components/ui/authButton";
import { SlackIcon } from "@/components/ui/icon";
import { useSupabase } from "@/lib/context/authProvider";
import { useOrganization } from "@/lib/context/orgProvider";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { SlackIntegration, StatusResponse } from "@/lib/types";
import { Axios } from "axios";
import { useEffect, useState } from "react";
import { FaSpinner } from "react-icons/fa";
import useSWR from "swr";

const slackIntegration = async ({
  axiosInstance,
  organizationId,
}: {
  axiosInstance: Axios;
  organizationId: string;
}): Promise<[boolean, string?]> => {
  try {
    const response = await axiosInstance.get(
      `/api/slack/install/${organizationId}?slack_integration_type=${SlackIntegration.USER}`
    );

    if (response.status === 200) {
      const authUrl = response.data.auth_url;
      window.location.href = authUrl;

      return [true];
    } else {
      const errorMsg = `Failed to setup OAuth for Slack - ${response.status}`;
      console.error(errorMsg);
      return [false, errorMsg];
    }
  } catch (error: any) {
    const errorMsg = `Failed to setup OAuth for Slack - ${error.message}`;
    console.error(errorMsg);
    return [false, errorMsg];
  }
};

export default function SlackConnectionPage() {
  const { session } = useSupabase();
  const { currentOrganization } = useOrganization();
  const shouldFetch = session !== null && currentOrganization?.id !== undefined
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isConnectingToSlack, setIsConnectingToSlack] = useState<boolean>(false);
  const [fetchedData, setFetchedData] = useState<StatusResponse | null>(null);
  //console.log(fetchedData)
  const { data, error, mutate } = useSWR(
    shouldFetch && fetchedData === null
      ? `/api/organization/${currentOrganization?.id}/verify-slack-users`
      : null,
    (url) => fetcher(url, axiosInstance)
  );
  // Once data is received, stop revalidating
  useEffect(() => {
    if (data) {
        setFetchedData(data);        
        setIsLoading(false);
    }
  }, [data, mutate]);

  const handleOnClick = async () => {
    setIsConnectingToSlack(true);
    try {
      const organizationId = currentOrganization?.id;
      if (organizationId === undefined) {
        throw new Error("Org ID is undefined");
      }

      const [success, errorMsg] = await slackIntegration({
        axiosInstance,
        organizationId: organizationId,
      });

      if (!success) {
        publish({
          variant: "danger",
          text: errorMsg!,
        });
      }
    } catch (error: any) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } finally {
      setIsConnectingToSlack(false);
    }
  };

  const content = isLoading ? (
    <div className="flex justify-center items-center">
      <div className="animate-spin h-5 w-5 text-white">
        <FaSpinner />
      </div>
    </div>
  ) : fetchedData?.success ? (
    <>
      <h3 className="text-lg font-medium">You're connected to Slack!</h3>
      <p className="text-sm text-muted-foreground">
        Call "/prosona" in Slack to start answering in your context and tone.
      </p>
    </>
  ) : (
    <>
      <h3 className="text-lg font-medium">Connect to Slack!</h3>
      <p className="text-sm text-muted-foreground">
        You're almost there! Click the button below to start using prosona
      </p>
      <AuthButton
        className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
        isLoading={isConnectingToSlack}
        onClick={handleOnClick}
      >
        <SlackIcon /> Add to Slack
      </AuthButton>
    </>
  );

  return <div>{content}</div>;
}
