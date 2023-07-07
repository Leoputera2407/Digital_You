"use client";
import AuthButton from "@/components/ui/AuthButton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
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
import { GithubIcon } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { createCredential, testGithubAccessToken } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import { useConnectorsOps } from "@/lib/hooks/useConnectorOps";
import {
  AnyCredentialJson,
  Connector,
  ConnectorBase,
  ConnectorIndexingStatus,
  Credential,
  GithubConfig,
  GithubCredentialJson,
  GithubTestBase,
  OrganizationBase,
} from "@/lib/types";
import { verifyValidParamString } from "@/lib/utils";
import { Axios } from "axios";
import { ChevronsUpDown } from "lucide-react";
import { FC, useState } from "react";
import { useForm } from "react-hook-form";
import { AiOutlineClose } from "react-icons/ai";
import { FaSpinner } from "react-icons/fa";
import { useGithubManyConnectors } from "./hook";

interface GithubConnectorProps {
  currentOrganization: OrganizationBase | null;
  connectorIndexingStatuses: ConnectorIndexingStatus<any>[] | undefined;
  credentialsData: Credential<AnyCredentialJson>[] | undefined;
  connectorsData: Connector<any>[] | undefined;
  isConnectorCredentialLoading: boolean;
}

interface InitialFormValues {
  accessTokenValue: string;
  repositoryUrl: string;
}

interface NewRepoFormValues {
  repositoryUrl: string;
}

interface InitialConnectFormProps {
  onSubmitUpsert: (data: {
    accessTokenValue: string;
    repositoryOwner: string;
    repositoryName: string;
  }) => Promise<void>;
  organizationId: string | undefined;
}
interface NewRepoFormProps {
  onSubmitUpsert: (data: {
    accessTokenValue: string;
    repositoryOwner: string;
    repositoryName: string;
  }) => Promise<void>;
  onSuccessUpsert: () => void;
  onCloseForm: () => void;
  githubAccessToken: string;
  axiosInstance: Axios;
  organizationId: string | undefined;
}

const githubConnectorNameBuilder = (
  repositoryOwner: string,
  repositoryName: string
): string => {
  return `GithubConnector-${repositoryOwner}/${repositoryName}`;
};

export const extractRepoInfoFromUrl = (
  url: string
): { repositoryOwner: string; repositoryName: string } | null => {
  const pattern = /\/([^\/]+)\/([^\/]+)/;
  const urlObject = new URL(url);
  const path = urlObject.pathname;
  const match = pattern.exec(path);

  if (urlObject.hostname !== "github.com") {
    return null;
  }

  if (match) {
    const [, repositoryOwner, repositoryName] = match;
    return { repositoryOwner, repositoryName };
  }
  return null;
};

const InitialConnectForm: FC<InitialConnectFormProps> = ({
  onSubmitUpsert,
  organizationId,
}) => {
  const [buttonState, setButtonState] = useState<"testing" | "store">(
    "testing"
  );
  const [testingText, setTestingText] = useState<string | null>(null);
  const { axiosInstance } = useAxios();

  const { register, handleSubmit } = useForm<InitialFormValues>();

  const onSubmitTest = async (data: {
    accessTokenValue: string;
    repositoryOwner: string;
    repositoryName: string;
  }) => {
    const githubTest: GithubTestBase = {
      repository_owner: data.repositoryOwner,
      repository_name: data.repositoryName,
      access_token_value: data.accessTokenValue,
    };

    try {
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined or null",
      });

      const { error } = await testGithubAccessToken(
        axiosInstance,
        githubTest,
        validOrganizationId
      );

      if (error) {
        console.log("Error while validating Github Access Token: ", error);
        setTestingText(`Error! ${error}`);
      } else {
        setButtonState("store");
        setTestingText(`Success! Access token is valid.`);
      }
    } catch (error: any) {
      console.log("Error: ", error);
      setTestingText(`Error! ${error.message}`);
    }
  };

  const onSubmit = (data: InitialFormValues) => {
    const urlValues = extractRepoInfoFromUrl(data.repositoryUrl);
    if (!urlValues) {
      setTestingText("Invalid Github repository URL!");
      return;
    }
    if (buttonState === "testing") {
      onSubmitTest({ ...data, ...urlValues });
    } else {
      onSubmitUpsert({
        accessTokenValue: data.accessTokenValue,
        ...urlValues,
      }).catch((error: any) => {
        setTestingText(`Error! ${error}`);
      });
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <AuthButton className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group">
          Connect
        </AuthButton>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Setup Github Access Token</DialogTitle>
            <DialogDescription>
              Enter your Github Access Token (Classic) below to pull GitHub
              issues and markdown documents from your repository.
              <br />
              <br />
              Unsure how to get it? Follow this&nbsp;
              <a
                href="https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="text-red-600 underline"
              >
                guide
              </a>
              .
              <br />
              <br />
              Ensure the Token has ✅ "repo" access.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="Github" className="text-right">
                Access Token
              </Label>
              <Input
                id="Github"
                {...register("accessTokenValue")}
                className="col-span-3"
              />

              <div className="col-span-4">
                <Label htmlFor="repositoryUrl" className="text-right">
                  Repository URL
                </Label>
                <Input
                  id="repositoryUrl"
                  {...register("repositoryUrl")}
                  className="col-span-3"
                />
              </div>

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

const NewRepoForm: FC<NewRepoFormProps> = ({
  onSubmitUpsert,
  onSuccessUpsert,
  onCloseForm,
  githubAccessToken,
  axiosInstance,
  organizationId,
}) => {
  const [buttonState, setButtonState] = useState<"testing" | "store">(
    "testing"
  );
  const [testingText, setTestingText] = useState<string | null>(null);

  const { register, handleSubmit } = useForm<NewRepoFormValues>();

  const onSubmitTest = async (data: {
    accessTokenValue: string;
    repositoryOwner: string;
    repositoryName: string;
  }) => {
    const githubTest: GithubTestBase = {
      repository_owner: data.repositoryOwner,
      repository_name: data.repositoryName,
      access_token_value: data.accessTokenValue,
    };

    try {
      const validOrganizationId = verifyValidParamString({
        param: organizationId,
        errorText: "Organization ID is undefined or null",
      });

      const { error } = await testGithubAccessToken(
        axiosInstance,
        githubTest,
        validOrganizationId
      );

      if (error) {
        console.log("Error while validating Github Access Token: ", error);
        setTestingText(`Error! ${error}`);
      } else {
        setButtonState("store");
        setTestingText(`Success! Access token is valid.`);
      }
    } catch (error: any) {
      console.log("Error: ", error);
      setTestingText(`Error! ${error.message}`);
    }
  };

  const onSubmit = (data: NewRepoFormValues) => {
    const urlValues = extractRepoInfoFromUrl(data.repositoryUrl);
    if (!urlValues) {
      setTestingText("Invalid Github repository URL!");
      return;
    }
    if (buttonState === "testing") {
      onSubmitTest({
        accessTokenValue: githubAccessToken,
        ...urlValues,
      });
    } else {
      onSubmitUpsert({
        accessTokenValue: githubAccessToken,
        ...urlValues,
      })
        .then(() => {
          onSuccessUpsert();
        })
        .catch((error: any) => {
          setTestingText(`Error! ${error}`);
        });
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="relative p-6 bg-gray-800 rounded text-white"
    >
      <button
        onClick={onCloseForm}
        className="absolute top-3 right-3 text-gray-300 hover:text-gray-500"
      >
        <AiOutlineClose size={24} />
      </button>
      <div className="flex items-center mt-4">
        <input
          type="text"
          {...register("repositoryUrl")}
          placeholder="Enter repository URL"
          className="p-2 flex-grow border rounded border-gray-700 mr-2 text-gray-200 placeholder-gray-500"
        />
        <button
          type="submit"
          className="py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {buttonState === "testing" ? "Test" : "Add"}
        </button>
      </div>
      {testingText && (
        <div
          className={
            buttonState === "testing"
              ? "text-red-500 mt-2"
              : "text-green-500 mt-2"
          }
        >
          {testingText}
        </div>
      )}
    </form>
  );
};

const GithubConnector: React.FC<GithubConnectorProps> = ({
  currentOrganization,
  connectorIndexingStatuses,
  credentialsData,
  connectorsData,
  isConnectorCredentialLoading,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isNewRepoFormVisible, setNewRepoFormVisible] = useState(false);
  const { axiosInstance } = useAxios();

  const {
    githubConnectorsInfo,
    githubPublicCredential,
    githubConnectorIndexingStatuses,
  } = useGithubManyConnectors({
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
  });

  const {
    revalidateCredentials,
    revalidateConnectors,
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

  const handleCreateLinkConnector = async (
    credentialId: number,
    repositoryOwner: string,
    repositoryName: string
  ) => {
    const connectorBase: ConnectorBase<GithubConfig> = {
      name: githubConnectorNameBuilder(repositoryOwner, repositoryName),
      input_type: "load_state",
      source: "github",
      connector_specific_config: {
        repo_owner: repositoryOwner,
        repo_name: repositoryName,
      },
      refresh_freq: 60 * 30, // 30 minutes
      disabled: true,
    };
    try {
      const connector = await handleCreateConnector(connectorBase);

      await handleLinkCredential(connector.id, credentialId);
      revalidateCredentials();
      revalidateIndexingStatus();
      revalidateConnectors();
    } catch (error: any) {
      throw new Error("Failed to Enable Connector!");
    }
  };

  const handleConnect = async (data: {
    accessTokenValue: string;
    repositoryOwner: string;
    repositoryName: string;
  }) => {
    try {
      if (!currentOrganization?.id) {
        throw new Error("Organization Id is not defined!");
      }
      const credential: Credential<GithubCredentialJson> =
        await createCredential({
          axiosInstance,
          publicDoc: true,
          credentialJson: {
            github_access_token: data.accessTokenValue,
          },
          organizationId: currentOrganization?.id,
        });
      await handleCreateLinkConnector(
        credential.id,
        data.repositoryOwner,
        data.repositoryName
      );
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
            {githubConnectorIndexingStatuses &&
              githubConnectorIndexingStatuses.length > 0 &&
              !isConnectorCredentialLoading &&
              githubPublicCredential && (
                <CollapsibleTrigger asChild>
                  <AuthButton className="hover:bg-accent hover:text-accent-foreground p-1">
                    <ChevronsUpDown className="h-6 w-6" />
                    <span className="sr-only">Toggle</span>
                  </AuthButton>
                </CollapsibleTrigger>
              )}
            <GithubIcon />
            <span>Github</span>
          </div>
        </div>
        {isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : githubPublicCredential === undefined &&
          (githubConnectorIndexingStatuses === undefined ||
            githubConnectorIndexingStatuses.length === 0) ? (
          <InitialConnectForm
            onSubmitUpsert={handleConnect}
            organizationId={currentOrganization?.id}
          />
        ) : (
          <div className="font-mono text-sm">
            <span className="font-bold">Access Token:</span>
            <span className="ml-2 text-gray-400">
              {githubPublicCredential!.credential_json.github_access_token}
            </span>
          </div>
        )}
      </div>

      <CollapsibleContent className="space-y-2">
        {githubConnectorsInfo &&
          githubConnectorsInfo.length > 0 &&
          githubConnectorIndexingStatuses &&
          githubConnectorIndexingStatuses.length > 0 &&
          !isConnectorCredentialLoading &&
          githubPublicCredential &&
          githubConnectorsInfo.map((connectorInfo, i) => {
            const { connector, indexingStatus, credentialIsLinked } =
              connectorInfo;
            const { repo_owner, repo_name } =
              connector.connector_specific_config;

            return (
              <div
                className="rounded-md border px-4 py-3 font-mono text-sm mb-4"
                key={i}
              >
                <div className="flex items-center justify-between space-x-4">
                  <span>
                    {repo_owner}/{repo_name}
                  </span>

                  {!isConnectorCredentialLoading &&
                    indexingStatus &&
                    credentialIsLinked && (
                      <div className="flex items-center space-x-4">
                        <ConnectorStatus
                          connectorIndexingStatus={indexingStatus}
                          hasCredentialsIssue={
                            indexingStatus.connector.credential_ids.length === 0
                          }
                        />
                        <AuthButton
                          className="text-sm bg-purple-500 hover:bg-purple-600 px-4 py-1 rounded shadow"
                          onClick={async (event) => {
                            event.preventDefault();
                            try {
                              await handleToggleConnector(connector);
                              revalidateConnectors();
                              revalidateIndexingStatus();
                            } catch (e) {
                              console.error(e);
                            }
                          }}
                          disabled={isLoadingConnectorOps}
                        >
                          {isLoadingConnectorOps ? (
                            <div className="animate-spin mr-2">
                              <FaSpinner className="h-5 w-5 text-white" />
                            </div>
                          ) : connector.disabled ? (
                            "Enable"
                          ) : (
                            "Disable"
                          )}
                        </AuthButton>
                      </div>
                    )}
                </div>
              </div>
            );
          })}
        {githubConnectorIndexingStatuses &&
          githubConnectorIndexingStatuses.length > 0 &&
          !isConnectorCredentialLoading &&
          githubPublicCredential && (
            <>
              {isNewRepoFormVisible ? (
                <NewRepoForm
                  onSubmitUpsert={(data) =>
                    handleCreateLinkConnector(
                      githubPublicCredential.id,
                      data.repositoryOwner,
                      data.repositoryName
                    )
                  }
                  onSuccessUpsert={() => setNewRepoFormVisible(false)}
                  onCloseForm={() => setNewRepoFormVisible(false)}
                  githubAccessToken={
                    githubPublicCredential.credential_json.github_access_token
                  }
                  organizationId={currentOrganization?.id}
                  axiosInstance={axiosInstance}
                />
              ) : (
                <AuthButton onClick={() => setNewRepoFormVisible(true)}>
                  Add New Repository
                </AuthButton>
              )}
            </>
          )}
      </CollapsibleContent>
    </Collapsible>
  );
};

export default GithubConnector;
