// Placeholder — will be overwritten by `npm run openapi:gen`.
// Until then we expose a minimal hand-typed surface so module APIs compile.

export type PageData<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type UserContext = {
  user_id: string;
  enterprise_email: string;
  role_id: string;
  role_name: string;
  cost_limit_amount: string;
  cost_limit_source: string;
  account_status: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type LoginSessionResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserContext;
  permissions: string[];
};

export type LoginChallengeResponse = {
  challenge_id: string;
  enterprise_email_mask: string;
  expires_at: string;
  dev_random_password?: string | null;
};

export type ProviderOut = {
  provider_id: string;
  provider_name: string;
  api_base_url: string;
  api_key_mask: string;
  api_description?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type ModelOut = {
  model_id: string;
  provider_id: string;
  provider_name: string;
  model_name: string;
  input_price_per_million_tokens: string;
  output_price_per_million_tokens: string;
  currency: string;
  status: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type OpenAPIOut = {
  openapi_id: string;
  api_name: string;
  api_type: 'OPENAI_COMPATIBLE' | 'ANTHROPIC_COMPATIBLE';
  gateway_url: string;
  usage_description?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type UserOut = {
  user_id: string;
  enterprise_email: string;
  role_id: string;
  role_name: string;
  cost_limit_source: string;
  cost_limit_amount: string;
  account_status: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type RoleOut = {
  role_id: string;
  role_name: string;
  permissions: string[];
  default_cost_limit_amount: string;
  api_key_validity_days: number;
  created_at: string;
  updated_at: string;
  version: number;
};

export type AdminAPIKeyOut = {
  api_key_id: string;
  owner_user_id: string;
  owner_enterprise_email: string;
  key_name: string;
  api_key_mask: string;
  application_date: string;
  expires_at: string;
  status: string;
  created_at: string;
  updated_at: string;
  version: number;
};

export type QuotaPolicyOut = {
  policy_id: string;
  reset_mode: 'MONTHLY' | 'NONE';
  reset_day_of_month?: number | null;
  reset_time?: string | null;
  timezone?: string | null;
  created_at: string;
  updated_at: string;
  version: number;
};

export type APIKeyOut = {
  api_key_id: string;
  owner_user_id: string;
  key_name: string;
  api_key_mask: string;
  application_date: string;
  expires_at: string;
  status: 'ENABLED' | 'DISABLED' | 'DELETED';
  created_at: string;
  updated_at: string;
  version: number;
};

export type APIKeyCreateResponse = {
  api_key: APIKeyOut;
  api_key_secret: string | null;
  api_key_secret_available: boolean;
  message?: string;
};

export type WorkbenchModelOut = {
  model_id: string;
  provider_id: string;
  provider_name: string;
  model_name: string;
  input_price_per_million_tokens: string;
  output_price_per_million_tokens: string;
  currency: string;
};

export type WorkbenchOpenAPIOut = {
  openapi_id: string;
  api_name: string;
  api_type: 'OPENAI_COMPATIBLE' | 'ANTHROPIC_COMPATIBLE';
  gateway_url: string;
  usage_description?: string | null;
};

export type TrendPoint = {
  period: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost: string;
};

export type ModelBreakdown = {
  model_id: string;
  model_name: string;
  total_tokens: number;
  total_cost: string;
};

export type PersonalConsumption = {
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost: string;
  currency: string;
  current_period_consumed: string;
  current_period_limit: string;
  quota_usage_ratio: number;
  trend: TrendPoint[];
  by_model: ModelBreakdown[];
};

export type RankingEntry = {
  rank: number;
  display_name: string;
  total_tokens: number;
  total_cost: string;
  is_current_user: boolean;
};

export type RankingResponse = {
  entries: RankingEntry[];
  total_users: number;
};

export type ConsumptionDetailRow = {
  usage_log_id: string;
  time: string;
  user_email: string;
  api_key_mask: string;
  model_name: string;
  input_tokens: number;
  output_tokens: number;
  cost: string;
  currency: string;
  status: string;
};

export type SummaryRow = {
  period: string;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost: string;
  currency: string;
  request_count: number;
};
