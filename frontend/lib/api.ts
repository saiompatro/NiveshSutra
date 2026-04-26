const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...rest } = options;
  const res = await fetch(`${BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(rest.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, token?: string) =>
    request<T>(path, { method: "GET", token }),

  post: <T>(path: string, body: unknown, token?: string) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body), token }),
};
