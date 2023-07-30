"use client";
import AuthButton from "@/components/ui/authButton";
import { Badge } from "@/components/ui/badge";
import { SlackIcon } from "@/components/ui/icon";
import { useSupabase } from "@/lib/context/authProvider";
import { useOrganization } from "@/lib/context/orgProvider";
import { fetcher } from "@/lib/fetcher";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import {
  Connector,
  SlackIntegration,
  SlackIntergrationUserResponse,
} from "@/lib/types";
import { Axios } from "axios";
import { useEffect, useRef, useState } from "react";
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
  const shouldFetch = session !== null && currentOrganization?.id !== undefined;
  const { axiosInstance } = useAxios();
  const { publish } = useToast();
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isConnectingToSlack, setIsConnectingToSlack] =
    useState<boolean>(false);
  const [fetchedData, setFetchedData] =
    useState<SlackIntergrationUserResponse | null>(null);
  const slackErrorPublishedRef = useRef(false);


  const {
    data: connectorsData,
    isLoading: isConnectorsLoading,
    error: isConnectorsError,
  } = useSWR<Connector<any>[]>(
    shouldFetch ? `/api/connector/${currentOrganization?.id}/list` : null,
    (url) => fetcher(url, axiosInstance)
  );

  const { data, error, mutate } = useSWR(
    shouldFetch && fetchedData === null
      ? `/api/organization/${currentOrganization?.id}/get-slack-users`
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


  useEffect(() => {
    let url = new URL(window.location.href);
    let searchParams = new URLSearchParams(url.search);
    let connectorType = searchParams.get("connector_type");
    let status = searchParams.get("status");
    let errorMessage = searchParams.get("error_message");
    
    async function refresh() {
      // remove query parameters from URL
      const location = window.location;
      const cleanUrl = `${location.protocol}//${location.host}${location.pathname}`;
      window.history.pushState({}, "", cleanUrl);
    }

    if (
      connectorType === "slack" &&
      status &&
      errorMessage
    ) {
      slackErrorPublishedRef.current = true;
      publish({
        variant: "danger",
        text: "Failed to connect to Slack: " + errorMessage,
      });
      refresh();
    }
  }, []);

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

  const slackConnector = connectorsData?.find(
    (connector) => connector.source === "slack"
  );

  const workspaceName = slackConnector?.connector_specific_config.workspace;

  const content = isLoading ? (
    <div className="flex justify-center items-center">
      <div className="animate-spin h-5 w-5 text-white">
        <FaSpinner />
      </div>
    </div>
  ) : slackConnector ? (
    fetchedData?.success ? (
      <div className="bg-slate-900 rounded-lg p-3 my-2 border border-gray-100 border-opacity-20">
        <h3 className="text-lg font-medium text-white mb-3">
          You're connected to Slack!
        </h3>
        <div className="p-3 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-gray-200">
              Workspace:
            </span>
            <span className="text-sm text-white">{workspaceName}</span>
          </div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-gray-200">
              Connected as:
            </span>
            <span className="text-sm text-white">
              {fetchedData?.data?.slack_user_name}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold text-gray-200">Email:</span>
            <span className="text-sm text-white">
              {fetchedData?.data?.slack_user_email}
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-400">
            Call "/prosona" in Slack to start answering in your context and
            tone.
          </p>
        </div>
      </div>
    ) : (
      <>
        <h3 className="text-lg font-medium mb-2">Connect to Slack!</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Your admin has enabled Prosona for{" "}
          <Badge className="bg-orange-200 text-orange-800">
            {workspaceName}
          </Badge>
          <br />
          You're almost there! Click the button below to start using Prosona.
        </p>
        <AuthButton
          className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-2 rounded shadow mb-4"
          isLoading={isConnectingToSlack}
          onClick={handleOnClick}
        >
          <div className="flex items-center">
            <SlackIcon />
            <span className="ml-2">Add to Slack</span>
          </div>
        </AuthButton>
      </>
    )
  ) : (
    <div className="text-white">
      <h3 className="font-semibold text-lg mb-2">Slack Connector Missing!</h3>
      <p>
        Slack hasn't been Connected yet. Please contact your Admin to add a
        SlackConnector to the Workspace.
      </p>
    </div>
  );

  return <div>{content}</div>;
}
