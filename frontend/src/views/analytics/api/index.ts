import { client } from '@/api/generated/client';
import type {
  ConsumptionDetailRow,
  PageData,
  PersonalConsumption,
  RankingResponse,
  SummaryRow,
} from '@/api/generated/types';

export const analyticsApi = {
  personal: (params: { period_type?: string; granularity?: string } = {}) => {
    const q = new URLSearchParams(params as Record<string, string>);
    return client.get<PersonalConsumption>(`/api/v1/analytics/personal-consumption?${q}`);
  },
  ranking: (period_type = 'CURRENT_ACCUMULATED') =>
    client.get<RankingResponse>(`/api/v1/analytics/consumption-ranking?period_type=${period_type}`),
  details: (params: { period_type?: string; page?: number; page_size?: number } = {}) => {
    const q = new URLSearchParams(params as Record<string, string>);
    return client.get<PageData<ConsumptionDetailRow>>(`/api/v1/analytics/consumption-details?${q}`);
  },
  summary: (granularity = 'DAY', period_type = 'CURRENT_ACCUMULATED') =>
    client.get<SummaryRow[]>(`/api/v1/analytics/consumption-summary?granularity=${granularity}&period_type=${period_type}`),
};
