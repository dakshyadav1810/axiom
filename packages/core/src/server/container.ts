import type { AxiomConfig } from "@axiom/shared";
import { CoreAuthoringService } from "../authoring/index.js";
import { EmptyKdgContextProvider } from "../authoring/kdg-context.js";
import { openDb } from "../cache/db.js";
import { SqliteCacheStore } from "../cache/index.js";
import { migrate } from "../cache/migrate.js";
import { PlaywrightTestRunner } from "../execution/dispatcher.js";
import { PlaywrightGroundingService } from "../grounding/index.js";
import { CoreHealingService } from "../healing/index.js";
import {
  CachedEmbedder,
  TransformersEmbeddingModel,
} from "../resolver/embeddings.js";
import { MultiSignalResolver } from "../resolver/index.js";
import { FsArtifactStore } from "../storage/index.js";

// Composition root — wires every subsystem behind its interface (invariant #8).
export function buildContainer(config: AxiomConfig) {
  const db = openDb(config.dbPath);
  migrate(db);
  const cache = new SqliteCacheStore(db);

  const embedder = new CachedEmbedder(
    new TransformersEmbeddingModel(config.embeddingModel),
    config.embeddingModel,
    cache,
  );
  const resolver = new MultiSignalResolver(embedder, config.bands);

  const store = new FsArtifactStore(config.artifactsDir);
  const grounding = new PlaywrightGroundingService(resolver, config);
  const kdg = new EmptyKdgContextProvider();
  const authoring = new CoreAuthoringService(kdg);
  const healing = new CoreHealingService(grounding, cache, authoring, store);
  const runner = new PlaywrightTestRunner(config, cache, healing);

  return {
    config,
    cache,
    store,
    resolver,
    grounding,
    authoring,
    healing,
    runner,
    kdg,
  };
}
export type Container = ReturnType<typeof buildContainer>;
