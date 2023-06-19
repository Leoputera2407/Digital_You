import { LinkBreakIcon, LinkIcon } from "@/components/ui/Icon";
import { updateConnector } from "@/lib/connectors";
import { useAxios } from "@/lib/hooks/useAxios";
import { useToast } from "@/lib/hooks/useToast";
import { Connector, ConnectorIndexingStatus } from "@/lib/types";
import type { User } from "@supabase/auth-helpers-nextjs";
import { ReactElement, useCallback, useState } from "react";

function getStatusDisplay<ConnectorConfigType> (
    connector: Connector<ConnectorConfigType>, 
    connectorIndexingStatus: ConnectorIndexingStatus<any>
): ReactElement {
  let statusDisplay: ReactElement;
  if (connector.disabled) {
    statusDisplay = <div className="text-red-700">Disabled</div>;
  } else {
    statusDisplay = connectorIndexingStatus.last_status === "failed"
      ? <div className="text-red-700">Failed</div>
      : <div className="text-emerald-600 flex">Enabled!</div>;
  }
  return statusDisplay;
};



interface ConnectorStatusProps<ConnectorConfigType> {
  connectorIndexingStatus: ConnectorIndexingStatus<ConnectorConfigType>;
  hasCredentialsIssue: boolean;
  user: User,
  onUpdate: () => void;
}

export function ConnectorStatus<ConnectorConfigType>({
  connectorIndexingStatus,
  hasCredentialsIssue,
  user,
  onUpdate,
}: ConnectorStatusProps<ConnectorConfigType>) {
  const [statusHovered, setStatusHovered] = useState<boolean>(false);
  const connector = connectorIndexingStatus.connector;
  const { publish } = useToast();
  const { axiosInstance } = useAxios();
  const statusDisplay = getStatusDisplay(connector, connectorIndexingStatus);

  const handleStatusHover = useCallback((value: boolean) => {
    setStatusHovered(value);
  }, []);

  const handleStatusClick = useCallback(() => {
    const updatedConnector = {
      ...connector,
      disabled: !connector.disabled,
    };
    updateConnector(axiosInstance, updatedConnector, user.id).then(() => {
      const message = `Connector ${connector.name} ${updatedConnector.disabled ? "enabled" : "disabled"}!`;
      publish({
        variant: "success",
        text: message,
      });
      onUpdate();
    });
  }, [connector, onUpdate, publish]);

  return (
    <div className="flex">
      {statusDisplay}
      {!hasCredentialsIssue && (
        <div
          className="cursor-pointer ml-1 my-auto relative"
          onMouseEnter={() => handleStatusHover(true)}
          onMouseLeave={() => handleStatusHover(false)}
          onClick={handleStatusClick}
        >
          {statusHovered && (
            <div className="flex flex-nowrap absolute top-0 left-0 ml-8 bg-gray-700 px-3 py-2 rounded shadow-lg">
              {connector.disabled ? "Enable!" : "Disable!"}
            </div>
          )}
          {connector.disabled ? (
            <LinkIcon className="my-auto flex flex-shrink-0 text-red-700" />
          ) : (
            <LinkBreakIcon
              className={`my-auto flex flex-shrink-0 ${
                connectorIndexingStatus.last_status === "failed"
                  ? "text-red-700"
                  : "text-emerald-600"
              }`}
            />
          )}
        </div>
      )}
    </div>
  );
}
