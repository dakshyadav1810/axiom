import type { FastifyInstance } from "fastify";
import type { WsHub } from "./ws-hub.js";

export async function registerWsRoutes(app: FastifyInstance, hub: WsHub) {
  app.get("/ws/runs/:id", { websocket: true }, (socket, req) => {
    const { id } = req.params as { id: string };
    const key = `run:${id}`;
    hub.subscribe(key, socket);
    socket.on("close", () => hub.unsubscribe(key, socket));
  });

  app.get("/ws/ground/:id", { websocket: true }, (socket, req) => {
    const { id } = req.params as { id: string };
    const key = `ground:${id}`;
    hub.subscribe(key, socket);
    socket.on("close", () => hub.unsubscribe(key, socket));
  });
}
