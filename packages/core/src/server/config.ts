import fs from "node:fs";
import { AxiomConfig } from "@axiom/shared";

export function loadConfig(): AxiomConfig {
  let fileConfig: Record<string, unknown> = {};
  try {
    fileConfig = JSON.parse(fs.readFileSync("axiom.config.json", "utf-8"));
  } catch {
    // no project config — defaults + env only
  }
  const envConfig = process.env.AXIOM_PORT
    ? { port: Number(process.env.AXIOM_PORT) }
    : {};
  return AxiomConfig.parse({ ...fileConfig, ...envConfig });
}
