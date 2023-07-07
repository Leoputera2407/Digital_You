"use client";

import { InfoIcon } from "@/components/ui/Icon";
import { ChevronsUpDown } from "lucide-react";
import * as React from "react";

import AuthButton from "@/components/ui/AuthButton";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/Collapsible";
import { Separator } from "@/components/ui/Separator";
import { useOrganization } from "@/lib/context/orgProvider";
import { useConnectorData } from "@/lib/hooks/useConnectorData";
import {
  AnyCredentialJson,
  ValidDataSourceTypesArray,
} from "@/lib/types";
import GoogleDriveConnector from "./google-drive/connector";
import NotionConnector from "./notion/connector";

const getDataSourceTypeDetails = (sourceType: string) => {
  switch (sourceType) {
    case "web":
      return {
        label: "Web",
        icon: <InfoIcon />,
      };
    default:
      throw new Error(`Unhandled source type: ${sourceType}`);
  }
};

export default function ConnectorMenuPage() {
  const [isOpenDataArr, setIsOpenDataArr] = React.useState(
    Array(ValidDataSourceTypesArray.length).fill(false)
  );
  const { currentOrganization } = useOrganization();
  console.log("currentOrganization", currentOrganization);
  const {
    isLoading: isConnectorCredentialLoading,
    isConnectorIndexingStatusesError,
    isConnectorsError,
    connectorIndexingStatuses,
    credentialsData,
    connectorsData,
  } = useConnectorData<AnyCredentialJson>(currentOrganization?.id || ""); 

  const handleOpenDataChange = (index: number, newState: boolean) => {
    const newArr = [...isOpenDataArr];
    newArr[index] = newState;
    setIsOpenDataArr(newArr);
  };

  return (
    <div className="min-h-screen w-full">
      {/* Connector Sources */}
      <div>
        <h3 className="text-lg font-medium">Connector Sources</h3>
        <p className="text-sm text-muted-foreground">
          Connector sources available to your apps.
        </p>
      </div>
      <Separator />
      <GoogleDriveConnector
        currentOrganization={currentOrganization}
        connectorIndexingStatuses={connectorIndexingStatuses}
        credentialsData={credentialsData}
        connectorsData={connectorsData}
        isConnectorCredentialLoading={isConnectorCredentialLoading}
      />
       <NotionConnector
        currentOrganization={currentOrganization}
        connectorIndexingStatuses={connectorIndexingStatuses}
        credentialsData={credentialsData}
        connectorsData={connectorsData}
        isConnectorCredentialLoading={isConnectorCredentialLoading}
      />
      

      {/* Data Sources */}
      <div className="mt-10">
        <h3 className="text-lg font-medium">Data Sources</h3>
        <p className="text-sm text-muted-foreground">
          Data sources available to your apps.
        </p>
      </div>
      <Separator />
      {ValidDataSourceTypesArray.map((sourceType, index) => {
        const sourceDetails = getDataSourceTypeDetails(sourceType);
        return (
          <Collapsible
            key={index}
            open={isOpenDataArr[index]}
            onOpenChange={(newState) => handleOpenDataChange(index, newState)}
            className="w-full space-y-2"
          >
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-2">
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="lg" className="p-1">
                    <ChevronsUpDown className="h-6 w-6" />
                    <span className="sr-only">Toggle</span>
                  </Button>
                </CollapsibleTrigger>
                <div className="flex items-center space-x-2">
                  {sourceDetails.icon}
                  <span>{sourceDetails.label}</span>
                </div>
                <Badge>Disabled</Badge>
              </div>
              <AuthButton className="btn text-sm text-white bg-purple-500 hover:bg-purple-600 shadow-sm group">
                Connect
              </AuthButton>
            </div>
            <CollapsibleContent className="space-y-2">
              <div className="rounded-md border px-4 py-3 font-mono text-sm">
                Content for {sourceType}
              </div>
            </CollapsibleContent>
          </Collapsible>
        );
      })}
    </div>
  );
}
