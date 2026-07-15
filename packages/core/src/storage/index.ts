import { randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import { CandidatesDoc, GroundedTest, SpecIR } from "@axiom/shared";
import { candidatesPath, groundedPath, specPath, testDir } from "./layout.js";

export interface TestSummary {
  testId: string;
  name: string;
  grounded: boolean;
}

export interface ArtifactStore {
  saveSpec(spec: SpecIR, testId?: string): Promise<string>;
  saveGrounded(testId: string, test: GroundedTest): Promise<void>;
  saveCandidates(testId: string, doc: CandidatesDoc): Promise<void>;
  loadSpec(testId: string): Promise<SpecIR>;
  loadGrounded(testId: string): Promise<GroundedTest>;
  list(): Promise<TestSummary[]>;
  delete(testId: string): Promise<void>;
}

// All writes re-validate against the shared Zod schema before hitting disk (fail closed on drift).
export class FsArtifactStore implements ArtifactStore {
  constructor(private artifactsDir: string) {}

  async saveSpec(spec: SpecIR, testId = randomUUID()): Promise<string> {
    const validated = SpecIR.parse(spec);
    await fs.mkdir(testDir(this.artifactsDir, testId), { recursive: true });
    await fs.writeFile(
      specPath(this.artifactsDir, testId),
      JSON.stringify(validated, null, 2),
    );
    return testId;
  }

  async saveGrounded(testId: string, test: GroundedTest): Promise<void> {
    const validated = GroundedTest.parse(test);
    await fs.mkdir(testDir(this.artifactsDir, testId), { recursive: true });
    await fs.writeFile(
      groundedPath(this.artifactsDir, testId),
      JSON.stringify(validated, null, 2),
    );
  }

  async saveCandidates(testId: string, doc: CandidatesDoc): Promise<void> {
    const validated = CandidatesDoc.parse(doc);
    await fs.mkdir(testDir(this.artifactsDir, testId), { recursive: true });
    await fs.writeFile(
      candidatesPath(this.artifactsDir, testId),
      JSON.stringify(validated, null, 2),
    );
  }

  async loadSpec(testId: string): Promise<SpecIR> {
    const raw = await fs.readFile(specPath(this.artifactsDir, testId), "utf-8");
    return SpecIR.parse(JSON.parse(raw));
  }

  async loadGrounded(testId: string): Promise<GroundedTest> {
    const raw = await fs.readFile(
      groundedPath(this.artifactsDir, testId),
      "utf-8",
    );
    return GroundedTest.parse(JSON.parse(raw));
  }

  async list(): Promise<TestSummary[]> {
    await fs.mkdir(this.artifactsDir, { recursive: true });
    const ids = await fs.readdir(this.artifactsDir);
    const out: TestSummary[] = [];
    for (const testId of ids) {
      try {
        const spec = await this.loadSpec(testId);
        const grounded = await fs
          .access(groundedPath(this.artifactsDir, testId))
          .then(() => true)
          .catch(() => false);
        out.push({ testId, name: spec.flow.name, grounded });
      } catch {
        // not a test dir (missing/invalid spec.json) — skip
      }
    }
    return out;
  }

  async delete(testId: string): Promise<void> {
    await fs.rm(testDir(this.artifactsDir, testId), {
      recursive: true,
      force: true,
    });
  }
}
