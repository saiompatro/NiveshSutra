import { createClient, type SupabaseClient, type User } from "@supabase/supabase-js";

function getSupabaseUrl() {
  return process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
}

function getSupabaseAnonKey() {
  return process.env.SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";
}

function getSupabaseServiceRoleKey() {
  return process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";
}

function assertEnv(name: string, value: string) {
  if (!value) {
    throw new Error(`${name} is not configured`);
  }
  return value;
}

export function hasSupabaseServiceRole() {
  return Boolean(getSupabaseServiceRoleKey());
}

export function createSupabaseAnonClient(accessToken?: string): SupabaseClient {
  const supabaseUrl = assertEnv("SUPABASE_URL", getSupabaseUrl());
  const supabaseAnonKey = assertEnv("SUPABASE_ANON_KEY", getSupabaseAnonKey());

  const headers: Record<string, string> = {};
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  return createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
    global: { headers },
  });
}

export function createSupabaseUserClient(accessToken: string): SupabaseClient {
  return createSupabaseAnonClient(accessToken);
}

export function createSupabaseAdminClient(): SupabaseClient {
  const supabaseUrl = assertEnv("SUPABASE_URL", getSupabaseUrl());
  const serviceRoleKey = assertEnv(
    "SUPABASE_SERVICE_ROLE_KEY",
    getSupabaseServiceRoleKey()
  );

  return createClient(supabaseUrl, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}

export async function requireSupabaseUser(authorizationHeader: string | null): Promise<{
  accessToken: string;
  user: User;
}> {
  if (!authorizationHeader?.startsWith("Bearer ")) {
    throw new Error("Authentication required");
  }

  const accessToken = authorizationHeader.slice("Bearer ".length).trim();
  if (!accessToken) {
    throw new Error("Authentication required");
  }

  const supabase = createSupabaseAnonClient();
  const { data, error } = await supabase.auth.getUser(accessToken);
  if (error || !data.user) {
    throw new Error(error?.message ?? "Invalid token");
  }

  return { accessToken, user: data.user };
}
