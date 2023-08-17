export enum UserRole {
  BASIC = "basic",
  ADMIN = "admin",
}

export enum SlackIntegration {
  CONNECTOR = "connector",
  USER = "user"
}
export interface GithubTestBase {
  access_token_value: string;
  repository_name: string;
  repository_owner: string;
}

export interface ConfluenceTestBase {
  confluence_access_token: string;
  confluence_username: string;
  wiki_page_url: string;
}

export interface OrganizationAssociationBase {
  id: string;
  name: string;
  role: UserRole;
  joined_at: string;
}

export interface OrganizationData {
  id: string;
  name: string;
};

export interface SlackIntegrationUserData {
  slack_user_name: string;
  slack_user_email: string;
  slack_team_name: string;
}

export interface StatusResponse {
  success: boolean;
  message: string;
}

export interface SlackIntergrationUserResponse extends StatusResponse {
  data: SlackIntegrationUserData | null;
}
export interface WhitelistDataResponse extends StatusResponse {
  data: OrganizationData[];
};

export interface OrganizationDataResponse extends StatusResponse {
  data: OrganizationData | null;
};

export interface VerifyOrgResponse extends StatusResponse {
  data: OrganizationAssociationBase | null;
}

export interface UserByEmail {
    user_email: string;
}

export interface UserAdminData extends UserByEmail {
  role: UserRole;
  user_id: string;
}

export interface InvitationBase {
    email: string;
    status: string;
}

export interface OrganizationAdminInfo{
  name: string;
  whitelisted_email_domain?: string;
  pending_invitations: InvitationBase[];
  users: UserAdminData[];
}

export interface OrganizationUpdateInfo{
  name?: string;
  whitelisted_email_domain?: string;
};

export interface UserOrgResponse {
  organizations: OrganizationAssociationBase[];
}



export type ValidSources =
  | "web"
  | "github"
  | "slack"
  | "google_drive"
  | "confluence"
  | "notion"
  | "linear"
  | "jira";

export const ValidConnectorSourceTypesArray: [ValidSources, ValidSources, ValidSources, ValidSources, ValidSources, ValidSources, ValidSources] = 
  ["google_drive", "notion", "github", "slack", "confluence", "linear", "jira"]

export const ValidDataSourceTypesArray: [ValidSources] 
  = ["web"]

export type ValidInputTypes = "load_state" | "poll" | "event";

export interface LinearOrganizationSnapshot {
  name: string;
  teams: {
    id: string;
    name: string;
  }[];
}

export interface NotionWorkspaceSnapshot {
  name: string;
}

// CONNECTORS
export interface ConnectorBase<T> {
  name: string;
  input_type: ValidInputTypes;
  source: ValidSources;
  connector_specific_config: T;
  refresh_freq: number;
  disabled: boolean;
}

export interface Connector<T> extends ConnectorBase<T> {
  id: number;
  user_id: string;
  credential_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface GithubConfig {
  repo_owner: string;
  repo_name: string;
}

export interface GoogleDriveConfig {
  is_public_connector: boolean;
  folder_paths?: string[];
}

export interface ConfluenceConfig {
  wiki_page_url: string;
}

export interface SlackConfig {
  workspace: string;
}
export interface JiraConfig {
  jira_project_url: string;
}
export interface LinearConfig {
  workspace: string;
  team_name: string;
  team_id: string;
}

export interface NotionConfig {
  workspace: string;
}

export interface ConnectorIndexingStatus<T> {
  connector: Connector<T>;
  owner: string;
  public_doc: boolean;
  last_status: "success" | "failed" | "in_progress" | "not_started";
  last_success: string | null;
  docs_indexed: number;
}

// CREDENTIALS
export interface CredentialBase<T> {
  credential_json: T;
  public_doc: boolean;
}

export interface Credential<T> extends CredentialBase<T> {
  id: number;
  user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface GithubCredentialJson {
  github_access_token: string;
}

export interface ConfluenceCredentialJson {
  confluence_username: string;
  confluence_access_token: string;
}

export interface SlackCredentialJson {
  slack_token: string;
}

export interface GoogleDriveCredentialJson {
  google_drive_tokens: string;
}

export interface NotionCredentialJson {
  notion_access_tokens: string;
}

export interface LinearCredentialJson {
  linear_access_tokens: string;
}

export interface JiraCredentialJson {
  jira_user_email: string;
  jira_api_token: string;
}

export type AnyCredentialJson = 
  | GithubCredentialJson 
  | ConfluenceCredentialJson 
  | SlackCredentialJson 
  | GoogleDriveCredentialJson
  | NotionCredentialJson 
  | LinearCredentialJson
  | JiraCredentialJson;

