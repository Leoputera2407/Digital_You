"use client";
import AuthButton from "@/components/ui/AuthButton";
import { Button } from "@/components/ui/Button";
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
import { SlackIcon } from "@/components/ui/Icon";
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
import { Axios } from "axios";
import { ChevronsUpDown } from "lucide-react";
import { FC, useState } from "react";
import { useForm } from "react-hook-form";
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
}
interface NewRepoFormProps {
  onSubmitUpsert: (data: {
    accessTokenValue: string;
    repositoryOwner: string;
    repositoryName: string;
  }) => Promise<void>;
  githubAccessToken: string;
  axiosInstance: Axios;
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
  const pattern = /github\.com\/([^\/]+)\/([^\/]+)/;
  const urlObject = new URL(url);
  const path = urlObject.pathname;
  const match = path.match(pattern);
  if (match) {
    const [, repositoryOwner, repositoryName] = match;
    return { repositoryOwner, repositoryName };
  }
  return null;
};

const InitialConnectForm: FC<InitialConnectFormProps> = ({ onSubmitUpsert }) => {
    const [buttonState, setButtonState] = useState<"testing" | "store">("testing");
    const [testingText, setTestingText] = useState<string | null>(null);
    const { axiosInstance } = useAxios();
  
    const { register, handleSubmit, getValues } = useForm<InitialFormValues>();
  
    const onSubmitTest = (data: {
      accessTokenValue: string;
      repositoryOwner: string;
      repositoryName: string;
    }) => {
      const githubTest: GithubTestBase = {
        repository_owner: data.repositoryOwner,
        repository_name: data.repositoryName,
        access_token_value: data.accessTokenValue,
      };
      testGithubAccessToken(axiosInstance, githubTest).then(({ error }) => {
        if (error) {
          console.log("Error while validating Github Access Token: ", error);
          setTestingText(`Error! ${error}`);
        } else {
          setButtonState("store");
          setTestingText(`Success! Access token is valid.`);
        }
      });
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
                Enter your Github Access Token here. We'll pull all the GitHub
                issues and markdown documents from this repository.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="Github" className="text-right">
                  Access Token
                </Label>
                <Input id="Github" {...register("accessTokenValue")} className="col-span-3" />
  
                <div className="col-span-4">
                  <Label htmlFor="repositoryUrl" className="text-right">
                    Repository URL
                  </Label>
                  <Input id="repositoryUrl" {...register("repositoryUrl")} className="col-span-3" />
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
              <Button type="submit">
                {buttonState === "testing" ? "Test" : "Enable"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    );
};

const NewRepoForm: FC<NewRepoFormProps> = ({
  onSubmitUpsert,
  githubAccessToken,
  axiosInstance,
}) => {
  const [buttonState, setButtonState] = useState<"testing" | "store">(
    "testing"
  );
  const [testingText, setTestingText] = useState<string | null>(null);

  const { register, handleSubmit } = useForm<NewRepoFormValues>();

  const onSubmitTest = (data: {
    repositoryOwner: string;
    repositoryName: string;
  }) => {
    const githubTest: GithubTestBase = {
      repository_owner: data.repositoryOwner,
      repository_name: data.repositoryName,
      access_token_value: githubAccessToken,
    };
    testGithubAccessToken(axiosInstance, githubTest).then(({ error }) => {
      if (error) {
        console.log("Error while validating Github Access Token: ", error);
        setTestingText(`Error! ${error}`);
      } else {
        setButtonState("store");
        setTestingText(`Success! Access token is valid.`);
      }
    });
  };

  const onSubmit = (values: NewRepoFormValues) => {
    const urlValues = extractRepoInfoFromUrl(values.repositoryUrl);
    if (!urlValues) {
      setTestingText("Invalid Github repository URL!");
      return;
    }
    if (buttonState === "testing") {
      onSubmitTest(urlValues);
    } else {
      onSubmitUpsert({
        accessTokenValue: githubAccessToken,
        ...urlValues,
      }).catch((error) => {
        setTestingText(`Error! ${error}`);
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="flex items-center">
        <input
          type="text"
          {...register("repositoryUrl")}
          placeholder="Enter repository URL"
        />
        <button type="submit">
          {buttonState === "testing" ? "Test" : "Enable"}
        </button>
      </div>
      {testingText && (
        <div
          className={
            buttonState === "testing" ? "text-red-500" : "text-green-500"
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
    revalidateIndexingStatus,
  } = useConnectorData(
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
                  <Button variant="ghost" size="lg" className="p-1">
                    <ChevronsUpDown className="h-6 w-6" />
                    <span className="sr-only">Toggle</span>
                  </Button>
                </CollapsibleTrigger>
              )}
            <SlackIcon />
            <span>Slack</span>
          </div>
        </div>
        {isConnectorCredentialLoading ? (
          <FaSpinner className="animate-spin" />
        ) : githubPublicCredential === undefined &&
          (githubConnectorIndexingStatuses === undefined ||
            githubConnectorIndexingStatuses.length === 0) ? (
          <InitialConnectForm onSubmitUpsert={handleConnect} />
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
                className="rounded-md border px-4 py-3 font-mono text-sm"
                key={i}
              >
                <div className="flex items-center space-x-2">
                  {repo_owner}/{repo_name}
                  {!isConnectorCredentialLoading &&
                    indexingStatus &&
                    credentialIsLinked && (
                      <ConnectorStatus
                        connectorIndexingStatus={indexingStatus}
                        hasCredentialsIssue={
                          indexingStatus.connector.credential_ids.length === 0
                        }
                      />
                    )}
                  <AuthButton
                    className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group"
                    onClick={async (event) => {
                      event.preventDefault();
                      try {
                        await handleToggleConnector(connector);
                        revalidateIndexingStatus();
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    isLoading={isLoadingConnectorOps}
                  >
                    {connector.disabled ? "Enable" : "Disable"}
                  </AuthButton>
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
                 onSubmitUpsert={
                    (data) => 
                    handleCreateLinkConnector(
                        githubPublicCredential.id, 
                        data.repositoryOwner, 
                        data.repositoryName
                    )
                  }
                  githubAccessToken={
                    githubPublicCredential.credential_json.github_access_token
                  }
                  axiosInstance={axiosInstance}                 
                />
              ) : (
                <Button onClick={() => setNewRepoFormVisible(true)}>
                  Add New Repository
                </Button>
              )}
            </>
          )}
      </CollapsibleContent>
    </Collapsible>
  );
};

export default GithubConnector;
