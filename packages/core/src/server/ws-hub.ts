import type { WsMessage } from "@axiom/shared";

type Socket = { send(data: string): void };

// In-memory pub/sub keyed by runId/testId so /ws/runs/:id and /ws/ground/:id can subscribe (LLD-008 §4).
export class WsHub {
  private subs = new Map<string, Set<Socket>>();

  subscribe(key: string, socket: Socket): void {
    if (!this.subs.has(key)) this.subs.set(key, new Set());
    this.subs.get(key)!.add(socket);
  }

  unsubscribe(key: string, socket: Socket): void {
    this.subs.get(key)?.delete(socket);
  }

  emit(key: string, message: WsMessage): void {
    for (const socket of this.subs.get(key) ?? []) {
      socket.send(JSON.stringify(message));
    }
  }
}
