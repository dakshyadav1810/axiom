import fs from "node:fs";
import { AxiomConfig } from "@axiom/shared";

// Precedence: CLI flags -> env -> axiom.config.json -> defaults (LLD-009 §6).
export function loadConfig(flags: Partial<AxiomConfig> = {}): AxiomConfig {
  let fileConfig: Record<string, unknown> = {};
  try {
    fileConfig = JSON.parse(fs.readFileSync("axiom.config.json", "utf-8"));
  } catch {
    // no project config
  }
  const envConfig = process.env.AXIOM_PORT
    ? { port: Number(process.env.AXIOM_PORT) }
    : {};
  return AxiomConfig.parse({ ...fileConfig, ...envConfig, ...flags });
}

export function baseUrl(config: AxiomConfig): string {
  return `http://127.0.0.1:${config.port}`;
}
