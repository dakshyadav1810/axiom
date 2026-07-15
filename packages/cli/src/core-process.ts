import fs from "node:fs";
import path from "node:path";
import type { AxiomConfig } from "@axiom/shared";
import { execa } from "execa";
import { baseUrl } from "./config.js";

const PID_FILE = path.join(".axiom", "axiom.pid");

async function waitForHealth(url: string, timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${url}/health`);
      if (res.ok) return;
    } catch {
      // core not up yet
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error(`core did not become healthy within ${timeoutMs}ms`);
}

// Spawns core as a child process, records its PID so `axiom stop` (any terminal) can find it (LLD-009 §3).
export async function startCore(config: AxiomConfig, coreEntry: string) {
  const child = execa("node", [coreEntry], {
    env: { ...process.env, AXIOM_PORT: String(config.port) },
    detached: true,
    stdio: "ignore",
  });
  fs.mkdirSync(".axiom", { recursive: true });
  fs.writeFileSync(PID_FILE, String(child.pid));
  child.unref();

  await waitForHealth(baseUrl(config), 15000);
  return child;
}

export function stopCore(): boolean {
  if (!fs.existsSync(PID_FILE)) return false;
  const pid = Number(fs.readFileSync(PID_FILE, "utf-8"));
  try {
    process.kill(pid, "SIGTERM");
  } catch {
    // already dead
  }
  fs.rmSync(PID_FILE, { force: true });
  return true;
}
