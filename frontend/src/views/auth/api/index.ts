import { client } from '@/api/generated/client';
import type {
  LoginChallengeResponse,
  LoginSessionResponse,
} from '@/api/generated/types';

export const authApi = {
  createChallenge: (enterprise_email: string) =>
    client.post<LoginChallengeResponse>('/api/v1/auth/login/challenges', { enterprise_email }),

  verifyChallenge: (challenge_id: string, enterprise_email: string, random_password: string) =>
    client.post<LoginSessionResponse>('/api/v1/auth/login/sessions', {
      challenge_id,
      enterprise_email,
      random_password,
    }),

  me: () => client.get<LoginSessionResponse>('/api/v1/auth/me'),
  logout: () => client.post('/api/v1/auth/logout'),
};
