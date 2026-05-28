import { client } from '@/api/generated/client';
import type {
  AdminAPIKeyOut,
  ModelOut,
  OpenAPIOut,
  PageData,
  ProviderOut,
  QuotaPolicyOut,
  RoleOut,
  UserOut,
} from '@/api/generated/types';

export const adminApi = {
  // providers
  listProviders: () => client.get<PageData<ProviderOut>>('/api/v1/admin/providers'),
  createProvider: (body: { provider_name: string; api_base_url: string; api_key: string; api_description?: string | null }) =>
    client.post<ProviderOut>('/api/v1/admin/providers', body),
  updateProvider: (id: string, body: Partial<{ provider_name: string; api_base_url: string; api_key: string; api_description: string }>) =>
    client.patch<ProviderOut>(`/api/v1/admin/providers/${id}`, body),
  deleteProvider: (id: string) => client.delete(`/api/v1/admin/providers/${id}`),

  // models
  listModels: () => client.get<PageData<ModelOut>>('/api/v1/admin/models'),
  createModel: (body: {
    provider_id: string;
    model_name: string;
    input_price_per_million_tokens: string;
    output_price_per_million_tokens: string;
    currency: string;
  }) => client.post<ModelOut>('/api/v1/admin/models', body),
  updateModel: (id: string, body: Partial<{ model_name: string; input_price_per_million_tokens: string; output_price_per_million_tokens: string; currency: string }>) =>
    client.patch<ModelOut>(`/api/v1/admin/models/${id}`, body),
  deleteModel: (id: string) => client.delete(`/api/v1/admin/models/${id}`),

  // openapis
  listOpenApis: () => client.get<PageData<OpenAPIOut>>('/api/v1/admin/enterprise-openapis'),
  createOpenApi: (body: { api_name: string; api_type: string; gateway_url: string; usage_description?: string | null }) =>
    client.post<OpenAPIOut>('/api/v1/admin/enterprise-openapis', body),
  updateOpenApi: (id: string, body: Partial<{ api_name: string; api_type: string; gateway_url: string; usage_description: string }>) =>
    client.patch<OpenAPIOut>(`/api/v1/admin/enterprise-openapis/${id}`, body),
  deleteOpenApi: (id: string) => client.delete(`/api/v1/admin/enterprise-openapis/${id}`),

  // users
  listUsers: () => client.get<PageData<UserOut>>('/api/v1/admin/users'),
  createUser: (body: {
    enterprise_email: string;
    role_id: string;
    cost_limit_source: string;
    custom_cost_limit_amount?: string | null;
    account_status: string;
  }) => client.post<UserOut>('/api/v1/admin/users', body),
  updateUser: (id: string, body: Partial<{ role_id: string; cost_limit_source: string; custom_cost_limit_amount: string; account_status: string }>) =>
    client.patch<UserOut>(`/api/v1/admin/users/${id}`, body),
  deleteUser: (id: string) => client.delete(`/api/v1/admin/users/${id}`),

  // roles
  listRoles: () => client.get<PageData<RoleOut>>('/api/v1/admin/roles'),
  listPermissionActions: () => client.get<string[]>('/api/v1/admin/roles/available-permissions'),
  createRole: (body: { role_name: string; permissions: string[]; default_cost_limit_amount: string; api_key_validity_days: number }) =>
    client.post<RoleOut>('/api/v1/admin/roles', body),
  updateRole: (id: string, body: Partial<{ role_name: string; permissions: string[]; default_cost_limit_amount: string; api_key_validity_days: number }>) =>
    client.patch<RoleOut>(`/api/v1/admin/roles/${id}`, body),
  deleteRole: (id: string) => client.delete(`/api/v1/admin/roles/${id}`),

  // api keys (admin)
  listApiKeys: () => client.get<PageData<AdminAPIKeyOut>>('/api/v1/admin/api-keys'),
  extendApiKey: (id: string, new_expires_at: string, reason: string) =>
    client.patch<AdminAPIKeyOut>(`/api/v1/admin/api-keys/${id}/expiry`, { new_expires_at, reason }),

  // quota policy
  getQuotaPolicy: () => client.get<QuotaPolicyOut>('/api/v1/admin/quota-reset-policy'),
  updateQuotaPolicy: (body: { reset_mode: string; reset_day_of_month?: number | null; reset_time?: string | null; timezone?: string | null }) =>
    client.put<QuotaPolicyOut>('/api/v1/admin/quota-reset-policy', body),
};
