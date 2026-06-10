export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_KEY = import.meta.env.VITE_API_KEY || '';

export function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return headers;
}

export async function apiGet(path: string, timeout = 30000): Promise<any> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      method: 'GET',
      headers: getHeaders(),
      signal: controller.signal
    });
    if (!response.ok) {
      throw await parseError(response);
    }
    return await response.json();
  } catch (error) {
    throw error;
  } finally {
    clearTimeout(id);
  }
}

export async function apiPost(path: string, data: any, timeout = 120000): Promise<any> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
      signal: controller.signal
    });
    if (!response.ok) {
      throw await parseError(response);
    }
    return await response.json();
  } catch (error) {
    throw error;
  } finally {
    clearTimeout(id);
  }
}

async function parseError(response: Response): Promise<Error> {
  try {
    const data = await response.json();
    return new Error(data.detail || JSON.stringify(data));
  } catch (e) {
    const text = await response.text();
    return new Error(text || `HTTP ${response.status}`);
  }
}
