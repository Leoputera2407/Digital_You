"use client";

import AuthButton from "@/components/ui/AuthButton";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import { GoogleDriveIcon } from "@/components/ui/Icon";
import type { ToastPublisher } from "@/components/ui/Toast/domain/types";
import { useSupabase } from "@/lib/auth/authProvider";
import {
  createConnector,
  deleteConnector,
  deleteCredential,
  linkCredential,
  unlinkCredential,
} from "@/lib/connectors";
import { fetcher } from "@/lib/fetcher";
import { setupGoogleDriveOAuth } from "@/lib/googleDrive";
import { useAxios } from "@/lib/hooks/useAxios";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useToast } from "@/lib/hooks/useToast";
import { ConnectorBase, GoogleDriveCredentialJson } from "@/lib/types";
import { redirect, useRouter } from "next/navigation";
import React, { useState } from "react";
import { FaSpinner } from "react-icons/fa";
import useSWR, { useSWRConfig } from "swr";

const LoadingSpinner = () => (
  <div className="mx-auto">
    <FaSpinner className="animate-spin" />
  </div>
);

interface FetchErrorProps {
  errorMsg: string;
  publish: ToastPublisher;
}

const FetchError: React.FC<FetchErrorProps> = ({ errorMsg, publish }) => {
  React.useEffect(() => {
    publish({ variant: "danger", text: errorMsg });
  }, []);

  return (
    <div className="text-red-500 text-center mt-5">
      <p>{errorMsg}</p>
    </div>
  );
};

const Main = () => {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { user } = useSupabase();
  const { publish } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const { axiosInstance } = useAxios();

  const {
    isLoading: isConnectorCredentialLoading,
    isConnectorIndexingStatusesError,
    isConnectorsError,
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
  } = useConnectorData<GoogleDriveCredentialJson>(user);

  const {
    data: appCredentialData,
    isLoading: isAppCredentialLoading,
    error: isAppCredentialError,
  } = useSWR<{ client_id: string }>(
    "/api/connector/google-drive/app-credential",
    fetcher
  );

  if (user?.id == undefined) {
    redirect("/signin");
  }

   // TODO: Grey out Button
   if (isConnectorCredentialLoading || isAppCredentialLoading) {
    return <LoadingSpinner />;
  }

  if (
    isAppCredentialError ||
    !appCredentialData ||
    isConnectorIndexingStatusesError ||
    !connectorIndexingStatuses ||
    !credentialsData
) {
    return (
      <FetchError
        errorMsg={
          isAppCredentialError || !appCredentialData
            ? "Error loading Google Drive app credentials. Contact an administrator."
            : isConnectorIndexingStatusesError || !connectorIndexingStatuses || !connectorsData || isConnectorsError
            ? "Failed to load data source connectors."
            : "Failed to load credentials."
        }
        publish={publish}
      />
    );
}
 

  const googleDrivePublicCredential = credentialsData?.find(
    (credential) =>
      credential.credential_json.google_drive_tokens && credential.public_doc
  );
  const googleDriveConnector = connectorsData?.find(
    (connector) => connector.source === "google_drive"
  );

  const googleDriveConnectorIndexingStatuses =
    connectorIndexingStatuses?.filter(
      (connectorIndexingStatus) =>
        connectorIndexingStatus.connector.source === "google_drive"
    );
  // Sorted by most recent 
  const googleDriveConnectorIndexingStatus =
    googleDriveConnectorIndexingStatuses?.[0];

  const credentialIsLinked =
    googleDriveConnectorIndexingStatus !== undefined &&
    googleDrivePublicCredential !== undefined &&
    googleDriveConnectorIndexingStatus.connector.credential_ids.includes(
      googleDrivePublicCredential.id
    );

  const handleDisconnect = async () => {
    setIsLoading(true);
    try {
      await unlinkCredential(
         axiosInstance, 
         googleDriveConnector?.id,
         googleDrivePublicCredential?.id,
         user.id
      );
      await deleteCredential(
        axiosInstance, 
        googleDrivePublicCredential?.id,
        user.id,
      );
      
      publish({
        variant: "success",
        text: "Successfully disconnected from Google Drive.",
      });
      mutate("/api/connector/credential");
    } catch (error: any) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthenticate = async () => {
    setIsLoading(true);
    try {
      const [authUrl, errorMsg] = await setupGoogleDriveOAuth({
        axiosInstance,
        supabaseUserId: user?.id,
        isPublic: true,
      });
    
      
      if (authUrl) {
        router.push(authUrl);
        return;
      }

      publish({
        variant: "danger",
        text: errorMsg,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConnector = async () => {
    setIsLoading(true);
    try {
      await deleteConnector(
        axiosInstance,
        googleDriveConnector?.id,
        user?.id
      );
      publish({
        variant: "success",
        text: "Successfully deleted connector!",
      });
      mutate("/api/connector/indexing-status");
    } catch (error: any) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } finally {
      setIsLoading(false);
    }
  };


  const handleCreateConnector = async () => {
    setIsLoading(true);
    const connectorBase: ConnectorBase<{}> = {
      name: "GoogleDriveConnector",
      input_type: "load_state",
      source: "google_drive",
      connector_specific_config: {},
      refresh_freq: 60 * 10, // 10 minutes
      disabled: false,
    };

    try {
      const connector = await createConnector(
        axiosInstance,
        connectorBase,
        user.id
      );
      await linkCredential(
        axiosInstance,
        connector.id,
        googleDrivePublicCredential?.id,
        user.id
      );
      publish({
        variant: "success",
        text: "Successfully created connector!",
      });
      mutate("/api/connector/indexing-status");
    } catch (error: any) {
      publish({
        variant: "danger",
        text: error.message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <GoogleDriveIcon />
      <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">Google Drive</h2>
      <div className="text-sm mb-4">
        {googleDrivePublicCredential ? (
          <>
            <p className="mb-2">
              <i>Disable This Specific Account!</i>
            </p>
            <AuthButton
              isLoading={isLoading}
              className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
              onClick={() =>
                handleDisconnect()
              }
            >
              Disconnect?
            </AuthButton>
          </>
        ) : (
          <>
            <p className="mb-2">
              This will give us permission to read your Google Drive files.
            </p>
            <AuthButton
              isLoading={isLoading}
              className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
              onClick={() => handleAuthenticate()}
            >
              Authenticate with Google Drive
            </AuthButton>
          </>
        )}
      </div>

      <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
        You're Succesfully connected
      </h2>
      {googleDrivePublicCredential ? (
        googleDriveConnectorIndexingStatus ? (
          credentialIsLinked ? (
            <div>
              <div className="text-sm mb-2">
                <div className="flex mb-1">
                  The Google Drive connector is made!{" "}
                  <b className="mx-2">Status:</b>{" "}
                  <ConnectorStatus
                    connectorIndexingStatus={googleDriveConnectorIndexingStatus}
                    hasCredentialsIssue={
                      googleDriveConnectorIndexingStatus.connector
                        .credential_ids.length === 0
                    }
                    user={user}
                    onUpdate={() => {
                      mutate("api/connector/indexing-status");
                    }}
                  />
                </div>
              </div>

              <p className="mb-2">
                 Click this button to delete connector.
                 This will remove all credentials too. Note, this is irreversible.
              </p>
              <AuthButton
                isLoading={isLoading}
                className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
                onClick={() => handleDeleteConnector()}
              >
                Delete Connector
              </AuthButton>

              <p className="mb-2">
                 Click this button to delete credential.
                 To connect to the same account, you would need to re-authenticate
              </p>
              <AuthButton
                isLoading={isLoading}
                className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
                onClick={() =>
                  handleDisconnect()
                }
              >
                Delete Credential
              </AuthButton>
            </div>
          ) : (
            <>
            </>
          )
        ) : (
          <>
            <p className="text-sm mb-2">
              Click the button below to create a connector. We will refresh the
              latest documents from Google Drive every <b>10</b> minutes.
            </p>
            <AuthButton
              isLoading={isLoading}
              className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 w-full shadow-sm group"
              onClick={() => handleCreateConnector()}
            >
              Add Data Source Connector
            </AuthButton>
          </>
        )
      ) : (
        <p className="text-sm">Please authenticate with Google Drive!</p>
      )}
    </>
  );
};

export default function Page() {
  return (
    <div className="mx-auto container">
      <div className="border-solid border-gray-600 border-b mb-4 pb-2 flex">
        <GoogleDriveIcon size="32" />
        <h1 className="text-3xl font-bold pl-2">Google Drive</h1>
      </div>
      <Main />
    </div>
  );
}
