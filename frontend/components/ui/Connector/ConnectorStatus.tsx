import { LinkBreakIcon, LinkIcon } from "@/components/ui/Icon";
import { Connector, ConnectorIndexingStatus } from "@/lib/types";
import dayjs from "dayjs";
import duration from "dayjs/plugin/duration";
import { ReactElement } from "react";
import { Badge } from "../Badge";

dayjs.extend(duration);  

function getStatusDisplay<ConnectorConfigType>(
  connector: Connector<ConnectorConfigType>,
  connectorIndexingStatus: ConnectorIndexingStatus<any>,
  hasCredentialsIssue: boolean
): ReactElement {
  let statusDisplay: ReactElement;

  if (connector.disabled) {
    statusDisplay = (
      <Badge className="bg-red-400 text-red-800">
        <div className="flex items-center">
          <LinkBreakIcon className="text-red-900 mr-2" />
          <span>Disabled</span>
        </div>
      </Badge>
    );
  } else if (
    connectorIndexingStatus.last_status === "failed" ||
    hasCredentialsIssue
  ) {
    statusDisplay = (
      <Badge className="bg-red-400 text-red-800">
        <div className="flex items-center">
          <LinkBreakIcon className="text-red-900 mr-2" />
          <span>Failed</span>
        </div>
      </Badge>
    );
  } else {
    statusDisplay = (
      <Badge className="bg-green-400 text-emerald-800">
        <div className="flex items-center">
          <LinkIcon className="text-emerald-900 mr-2" />
          <span>Enabled!</span>
        </div>
      </Badge>
    );
  }

  return statusDisplay;
}


function getFormattedTimeDifference(lastSuccess: string): string {
  const now = dayjs();
  const lastSuccessDate = dayjs(lastSuccess);
  const diff = dayjs.duration(now.diff(lastSuccessDate));

  if (diff.asDays() >= 1) {
    return `${Math.round(diff.asDays())} day(s) ago`;
  } else if (diff.asHours() >= 1) {
    return `${Math.round(diff.asHours())} hour(s) ago`;
  } else if (diff.asMinutes() >= 1) {
    return `${Math.round(diff.asMinutes())} minute(s) ago`;
  } else {
    return `${Math.round(diff.asSeconds())} second(s) ago`;
  }
}
interface ConnectorStatusProps<ConnectorConfigType> {
  connectorIndexingStatus: ConnectorIndexingStatus<ConnectorConfigType>;
  hasCredentialsIssue: boolean;
}

export function ConnectorStatus<ConnectorConfigType>({
  connectorIndexingStatus,
  hasCredentialsIssue,
}: ConnectorStatusProps<ConnectorConfigType>) {
  const connector = connectorIndexingStatus.connector;
  const statusDisplay = getStatusDisplay(
    connector,
    connectorIndexingStatus,
    hasCredentialsIssue
  );
  const updateTime = connectorIndexingStatus.last_success ? 
    getFormattedTimeDifference(connectorIndexingStatus.last_success) : null;

    return (
      <div className="flex flex-col">
        {statusDisplay}
        {updateTime && <p className="text-sm text-gray-500 mt-2">Last updated: {updateTime}</p>}
      </div>
    );
}
