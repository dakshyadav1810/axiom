import path from "node:path";
import type { AxiomConfig } from "@axiom/shared";
import fastifyStatic from "@fastify/static";
import fastifyWebsocket from "@fastify/websocket";
import Fastify from "fastify";
import {
  type ZodTypeProvider,
  serializerCompiler,
  validatorCompiler,
} from "fastify-type-provider-zod";
import type { Container } from "./container.js";
import { registerRoutes } from "./routes.js";
import { WsHub } from "./ws-hub.js";
import { registerWsRoutes } from "./ws-routes.js";

export async function buildApp(config: AxiomConfig, container: Container) {
  const app = Fastify({ logger: true }).withTypeProvider<ZodTypeProvider>();
  app.setValidatorCompiler(validatorCompiler);
  app.setSerializerCompiler(serializerCompiler);

  await app.register(fastifyWebsocket);
  await app.register(fastifyStatic, {
    root: path.join(import.meta.dirname, "..", "static"),
    prefix: "/",
  });

  const hub = new WsHub();
  await registerRoutes(app, container, hub);
  await registerWsRoutes(app, hub);

  app.setErrorHandler((err: Error & { statusCode?: number }, _req, reply) => {
    reply
      .code(err.statusCode ?? 500)
      .send({ error: { code: "validation", message: err.message } });
  });

  return app;
}
