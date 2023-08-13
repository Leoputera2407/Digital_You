"use client";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import AuthButton from "@/components/ui/authButton";
import { Collapsible } from "@/components/ui/collapsible";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ConfluenceIcon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createCredential, testConfluenceAccessToken } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import {
  AnyCredentialJson,
  ConfluenceConfig,
  ConfluenceCredentialJson,
  ConfluenceTestBase,
  Connector,
  ConnectorBase,
  ConnectorIndexingStatus,
  Credential,
  OrganizationAssociationBase,
} from "@/lib/types";
import { verifyValidParamString } from "@/lib/utils";
import { FC, useState } from "react";
import { useForm } from "react-hook-form";
import { FaSpinner } from "react-icons/fa";
import { useConfluenceConnectors } from "./hook";

interface ConfluenceConnectorProps {
  currentOrganization: OrganizationAssociationBase | null;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

interface FormValues {
  accessTokenValue: string;
  userName: string;
  wikiUrl: string;
}
interface InitialConnectFormProps {
  onSubmitUpsert: (data: any) => void;
  organizationId: string | undefined;
}

const confluenceConnectorNameBuilder = (wiki_page_url: string): string => {
  return `ConfluenceConnector-${wiki_page_url}`;
};

const InitialConnectForm: FC<InitialConnectFormProps> = ({
  onSubmitUpsert,
  organizationId,
}) => {
  const [buttonState, setButtonState] = useState<"testing" | "store">(
    "testing"
  );
  const [testingText, setTestingText] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState<boolean>(false);

  const { axiosInstance } = useAxios();

  const { register, handleSubmit } = useForm<FormValues>();

  const onSubmitTest = async (data: {
    accessTokenValue: string;
    userName: string;
    wikiUrl: string;
  }) => {
    try {
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined or null",
      });

      const confluenceTest: ConfluenceTestBase = {
        confluence_access_token: data.accessTokenValue,
        confluence_username: data.userName,
        wiki_page_url: data.wikiUrl,
      };

      const { error } = await testConfluenceAccessToken(
        axiosInstance,
        confluenceTest,
        validOrganizationId
      );

      if (error) {
        console.log("Error while validating Confluence Access Token: ", error);
        setTestingText(`Error! ${error}`);
      } else {
        setButtonState("store");
        setTestingText(`Success! Access token is valid.`);
      }
    } catch (error) {
      console.log("Error while validating Confluence Access Token: ", error);
      setTestingText(`Error! ${error}`);
    }
  };

  const onSubmit = async (data: FormValues) => {
    if (buttonState === "testing") {
      await onSubmitTest(data);
    } else {
      try {
        await onSubmitUpsert(data);
        setIsDialogOpen(false);
      } catch (error: any) {
        console.error("Error: ", error);
        setTestingText(`Error! ${error}`);
      }
    }
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <AuthButton className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow">
          Connect
        </AuthButton>
      </DialogTrigger>
      <DialogContent className="bg-black sm:max-w-[425px]">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Setup Confluence Connector</DialogTitle>
            <DialogDescription>
              Enter your Confluence Email and API Token here. We'll pull all the
              documentation from the given Confluence Wiki URL. To get the API
              Token, follow this &nbsp;
              <a
                href="https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account"
                target="_blank"
                rel="noopener noreferrer"
                className="text-red-600 underline"
              >
                guide
              </a>
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="UserName" className="text-right">
                Confluence Email
              </Label>
              <Input
                id="UserName"
                {...register("userName")}
                className="col-span-3"
                placeholder="your-name@domain.com"
              />

              <Label htmlFor="WikiUrl" className="text-right">
                Wiki URL
              </Label>

              <Input
                id="WikiUrl"
                {...register("wikiUrl")}
                className="col-span-3"
                placeholder="https://your-domain.atlassian.net/wiki/spaces/SPACE_NAME/..."
              />

              <div className="col-start-2 col-span-3">
                <p className="text-xs text-white pl-4 pt-1 italic">
                  The URL should include "wiki/spaces/SPACE_NAME".
                </p>
              </div>
              <Label htmlFor="AccessTokenValue" className="text-right">
                API Token
              </Label>
              <Input
                id="AccessTokenValue"
                {...register("accessTokenValue")}
                className="col-span-3"
              />

              {testingText && (
                <div
                  className={
                    buttonState === "testing"
                      ? "text-red-500"
                      : "text-green-500"
                  }
                >
                  {testingText}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <AuthButton type="submit">
              {buttonState === "testing" ? "Test" : "Enable"}
            </AuthButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const ConfluenceConnector: React.FC<ConfluenceConnectorProps> = ({
  currentOrganization,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { axiosInstance } = useAxios();

  const {
    confluenceConnectorIndexingStatus,
    confluencePublicCredential,
    confluenceConnector,
    credentialIsLinked: isConfluenceCredentialLinked,
  } = useConfluenceConnectors({
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
  });

  const {
    revalidateConnectors,
    revalidateCredentials,
    revalidateIndexingStatus,
  } = useConnectorData(currentOrganization?.id);

  const {
    isLoading: isLoadingConnectorOps,
    handleCreateConnector,
    handleLinkCredential,
    handleToggleConnector,
  } = useConnectorsOps(currentOrganization?.id);

  const handleToggleOpen = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const handleConnect = async (data: {
    accessTokenValue: string;
    userName: string;
    wikiUrl: string;
  }) => {
    const connectorBase: ConnectorBase<ConfluenceConfig> = {
      name: confluenceConnectorNameBuilder(data.wikiUrl),
      input_type: "load_state",
      source: "confluence",
      connector_specific_config: {
        wiki_page_url: data.wikiUrl,
      },
      refresh_freq: 60 * 30, // 30 minutes
      disabled: true,
    };
    try {
      if (!currentOrganization?.id) {
        throw new Error("Organization Id is not defined!");
      }
      const credential: Credential<ConfluenceCredentialJson> =
        await createCredential({
          axiosInstance,
          publicDoc: true,
          credentialJson: {
            confluence_username: data.userName,
            confluence_access_token: data.accessTokenValue,
          },
          organizationId: currentOrganization?.id,
        });
      const connector = await handleCreateConnector(connectorBase);

      await handleLinkCredential(connector.id, credential.id);
      revalidateIndexingStatus();
      revalidateCredentials();
      revalidateConnectors();
    } catch (error: any) {
      throw new Error("Failed to Connect!");
    }
  };
  return (
    <Collapsible
      open={isOpen}
      onOpenChange={handleToggleOpen}
      className="w-full space-y-2"
    >
      <div className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-2">
          <ConfluenceIcon />
          <span>Confluence</span>
        </div>
        <div className="flex items-center space-x-4">
          {!isConnectorCredentialLoading &&
            confluenceConnectorIndexingStatus &&
            confluencePublicCredential &&
            isConfluenceCredentialLinked && (
              <ConnectorStatus
                connectorIndexingStatus={confluenceConnectorIndexingStatus}
                hasCredentialsIssue={
                  confluenceConnectorIndexingStatus.connector.credential_ids
                    .length === 0
                }
              />
            )}

          {isConnectorCredentialLoading ? (
            <div className="animate-spin mr-2">
              <FaSpinner className="h-5 w-5 text-white" />
            </div>
          ) : confluencePublicCredential === undefined ||
            confluenceConnectorIndexingStatus === undefined ||
            confluenceConnector === undefined ? (
            <InitialConnectForm
              onSubmitUpsert={handleConnect}
              organizationId={currentOrganization?.id}
            />
          ) : (
            <AuthButton
              className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
              onClick={async (event) => {
                event.preventDefault();
                try {
                  await handleToggleConnector(confluenceConnector!);
                  revalidateConnectors();
                  revalidateIndexingStatus();
                } catch (e) {
                  console.error(e);
                }
              }}
              isLoading={isLoadingConnectorOps}
            >
              <div className="inline-flex items-center justify-center">
                {confluenceConnector!.disabled ? "Enable" : "Disable"}
              </div>
            </AuthButton>
          )}
        </div>
      </div>
    </Collapsible>
  );
};

export default ConfluenceConnector;
