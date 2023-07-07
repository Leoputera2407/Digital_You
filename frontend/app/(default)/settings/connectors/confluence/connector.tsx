"use client";
import AuthButton from "@/components/ui/AuthButton";
import { Button } from "@/components/ui/Button";
import {
  Collapsible
} from "@/components/ui/Collapsible";
import { ConnectorStatus } from "@/components/ui/Connector/ConnectorStatus";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/Dialog";
import { ConfluenceIcon } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
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
  OrganizationBase,
} from "@/lib/types";
import { FC, useState } from "react";
import { useForm } from "react-hook-form";
import { FaSpinner } from "react-icons/fa";
import { useConfluenceConnectors } from "./hook";

interface ConfluenceConnectorProps {
  currentOrganization: OrganizationBase | null;
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
}

const confluenceConnectorNameBuilder = (wiki_page_url: string): string => {
  return `ConfluenceConnector-${wiki_page_url}`;
};

const InitialConnectForm: FC<InitialConnectFormProps> = ({
  onSubmitUpsert,
}) => {
  const [buttonState, setButtonState] = useState<"testing" | "store">(
    "testing"
  );
  const [testingText, setTestingText] = useState<string | null>(null);
  const { axiosInstance } = useAxios();

  const { register, handleSubmit } = useForm<FormValues>();

  const onSubmitTest = (data: {
    accessTokenValue: string;
    userName: string;
    wikiUrl: string;
  }) => {
    const confluenceTest: ConfluenceTestBase = {
      confluence_access_token: data.accessTokenValue,
      confluence_username: data.userName,
      wiki_page_url: data.wikiUrl,
    };
    testConfluenceAccessToken(axiosInstance, confluenceTest).then(
      ({ error }) => {
        if (error) {
          console.log(
            "Error while validating Confluence Access Token: ",
            error
          );
          setTestingText(`Error! ${error}`);
        } else {
          setButtonState("store");
          setTestingText(`Success! Access token is valid.`);
        }
      }
    );
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <AuthButton className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group">
          Connect
        </AuthButton>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <form
          onSubmit={handleSubmit(
            buttonState === "testing" ? onSubmitTest : onSubmitUpsert
          )}
        >
          <DialogHeader>
            <DialogTitle>Setup Confluence Connector</DialogTitle>
            <DialogDescription>
              Enter your Confluence User Name and Access Token here. We'll pull
              all the documentation in from the given Confluence Wiki URL.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="UserName" className="text-right">
                User Name
              </Label>
              <Input
                id="UserName"
                {...register("userName")}
                className="col-span-3"
              />

              <Label htmlFor="WikiUrl" className="text-right">
                Wiki URL
              </Label>
              <Input
                id="WikiUrl"
                {...register("wikiUrl")}
                className="col-span-3"
              />

              <Label htmlFor="AccessTokenValue" className="text-right">
                Access Token
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
            <Button type="submit">
              {buttonState === "testing" ? "Test" : "Enable"}
            </Button>
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

  const { revalidateCredentials, revalidateIndexingStatus } = useConnectorData(
    currentOrganization?.id
  );

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
      name: confluenceConnectorNameBuilder(
        data.wikiUrl
      ),
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
          <div className="flex items-center space-x-2">
            <ConfluenceIcon />
            <span>Confluence</span>
          </div>
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
        </div>

        {isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : confluencePublicCredential === undefined &&
          confluenceConnectorIndexingStatus === undefined  &&
          confluenceConnector === undefined 
            ? (
           <InitialConnectForm onSubmitUpsert={handleConnect} />
         )  : (
          <AuthButton
            className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
            onClick={async (event) => {
              event.preventDefault();
              try {
                await handleToggleConnector(confluenceConnector!);
                revalidateIndexingStatus();
              } catch (e) {
                console.error(e);
              }
            }}
            isLoading={isLoadingConnectorOps}
          >
            {confluenceConnector?.disabled ? "Enable" : "Disable"}
          </AuthButton>
        )}
      </div>
    </Collapsible>
  );
};

export default ConfluenceConnector;
