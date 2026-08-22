/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

export interface HealthResponse {
  status: string;
  appId: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) {
    throw new Error(`API health check failed (${response.status}).`);
  }
  return response.json() as Promise<HealthResponse>;
}
