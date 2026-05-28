import { client } from '@/api/generated/client';
import type {
  APIKeyCreateResponse,
  APIKeyOut,
  PageData,
  WorkbenchModelOut,
  WorkbenchOpenAPIOut,
} from '@/api/generated/types';

export const workbenchApi = {
  listKeys: () => client.get<PageData<APIKeyOut>>('/api/v1/workbench/api-keys'),
  createKey: (key_name: string, expires_at: string) =>
    client.post<APIKeyCreateResponse>('/api/v1/workbench/api-keys', { key_name, expires_at }),
  setStatus: (id: string, status: 'ENABLED' | 'DISABLED') =>
    client.patch<APIKeyOut>(`/api/v1/workbench/api-keys/${id}/status`, { status }),
  deleteKey: (id: string) => client.delete(`/api/v1/workbench/api-keys/${id}`),
  listModels: () => client.get<PageData<WorkbenchModelOut>>('/api/v1/workbench/models'),
  listOpenApis: () => client.get<PageData<WorkbenchOpenAPIOut>>('/api/v1/workbench/enterprise-openapis'),
};
