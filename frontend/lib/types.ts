export enum UserRole {
  BASIC = "basic",
  ADMIN = "admin",
}

export interface OrganizationBase {
  id: string;
  name: string;
  role: UserRole;
  joined_at: string;
}

export interface UserOrgResponse {
  organizations: OrganizationBase[];
}

export type SupportedModels = "GPT3_5" | "GPT4" | "ANTROPHIC";
export const SupportedModelsArray: [SupportedModels, SupportedModels, SupportedModels] = ["GPT3_5", "GPT4", "ANTROPHIC"];

export type APIKeyType = "anthrophic_api_key" | "openai_api_key" | "slack_bot_key";
export const ModelAPIKeyTypesArray: [APIKeyType, APIKeyType] = ["anthrophic_api_key", "openai_api_key"];

export type ValidSources =
  | "web"
  | "github"
  | "slack"
  | "google_drive"
  | "confluence"
  | "notion";

export const ValidConnectorSourceTypesArray: [ValidSources, ValidSources, ValidSources, ValidSources, ValidSources] = 
  ["google_drive", "notion", "github", "slack", "confluence"]

export const ValidDataSourceTypesArray: [ValidSources] 
  = ["web"]

export type ValidInputTypes = "load_state" | "poll" | "event";

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
  github_access_tokens: string;
}

export interface ConfluenceCredentialJson {
  confluence_username: string;
  confluence_access_token: string;
}

export interface SlackCredentialJson {
  slack_bot_token: string;
}

export interface GoogleDriveCredentialJson {
  google_drive_tokens: string;
}

export interface NotionCredentialJson {
  notion_access_tokens: string;
}

export type AnyCredentialJson = 
  | GithubCredentialJson 
  | ConfluenceCredentialJson 
  | SlackCredentialJson 
  | GoogleDriveCredentialJson
  | NotionCredentialJson;


export interface APIKeyJson {
  key_type: APIKeyType;
  key_value: string;
}

export interface BaseModelJson {
  supported_model_enum: SupportedModels;
  temperature: number;
}

