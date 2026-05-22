import { apiRequest, setTokens } from './client';
import type { HRUser, TokenPair } from '../types/api';

export async function login(email: string, password: string): Promise<TokenPair> {
  const tokens = await apiRequest<TokenPair>('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    skipAuth: true,
    skipRefresh: true,
  });
  setTokens(tokens.access, tokens.refresh);
  return tokens;
}

export async function getMe(): Promise<HRUser> {
  return apiRequest<HRUser>('/api/auth/me/');
}
