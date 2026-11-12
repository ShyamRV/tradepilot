/**
 * Typed Neon env for Node tooling / Next server code.
 * Requires vars already injected (`.env.local` via `neon deploy` / `neon env pull`,
 * or `neon-env run -- …`). Prefer pooled DATABASE_URL for app traffic.
 */
import { parseEnv } from "@neon/env";
import config from "../neon";

/** Pooled Postgres URL for the API / app (not migrations). */
export function neonPostgres() {
  const { postgres } = parseEnv(config, ["DATABASE_URL"]);
  return postgres;
}

/** Branch identity + pooled URL when needed by Next/server scripts. */
export function neonAppEnv() {
  return parseEnv(config, ["DATABASE_URL", "NEON_BRANCH", "NEON_BRANCH_ID"]);
}
