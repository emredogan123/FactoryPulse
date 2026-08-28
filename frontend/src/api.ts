import axios from 'axios'


import type {
  AnalyticsOverview,
  PCBRiskPrediction,
  PCBUnit,
  TokenResponse,
  User,
  PCBRiskListResponse,
  ModelPerformance,
} from './types'

const TOKEN_STORAGE_KEY =
  'factorypulse_access_token'

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15_000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(
    TOKEN_STORAGE_KEY,
  )

  if (token) {
    config.headers.Authorization =
      `Bearer ${token}`
  }

  return config
})

export function getStoredToken(): string | null {
  return localStorage.getItem(
    TOKEN_STORAGE_KEY,
  )
}

export function storeToken(token: string): void {
  localStorage.setItem(
    TOKEN_STORAGE_KEY,
    token,
  )
}

export function clearToken(): void {
  localStorage.removeItem(
    TOKEN_STORAGE_KEY,
  )
}

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const body = new URLSearchParams()

  body.set('username', email)
  body.set('password', password)

  const response = await api.post<TokenResponse>(
    '/auth/login',
    body,
    {
      headers: {
        'Content-Type':
          'application/x-www-form-urlencoded',
      },
    },
  )

  return response.data
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>(
    '/auth/me',
  )

  return response.data
}

export async function getAnalyticsOverview():
Promise<AnalyticsOverview> {
  const response =
    await api.get<AnalyticsOverview>(
      '/analytics/overview',
    )

  return response.data
}

export async function getPCBUnits():
Promise<PCBUnit[]> {
  const response = await api.get<PCBUnit[]>(
    '/pcb-units',
  )

  return response.data
}

export async function getPCBRisk(
  pcbId: string,
): Promise<PCBRiskPrediction> {
  const response =
    await api.get<PCBRiskPrediction>(
      `/analytics/pcbs/${pcbId}/risk`,
    )

  return response.data
}

export async function getPCBRisks(
  prefix = 'ML-TEST',
  limit = 50,
): Promise<PCBRiskListResponse> {
  const response =
    await api.get<PCBRiskListResponse>(
      '/analytics/pcb-risks',
      {
        params: {
          prefix,
          limit,
        },
      },
    )

  return response.data
}

export async function getModelPerformance():
Promise<ModelPerformance> {
  const response =
    await api.get<ModelPerformance>(
      '/analytics/model-performance',
    )

  return response.data
}