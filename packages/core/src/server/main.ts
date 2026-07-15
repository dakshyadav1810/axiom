import { buildApp } from "./app.js";
import { loadConfig } from "./config.js";
import { buildContainer } from "./container.js";

const config = loadConfig();
const container = buildContainer(config);
const app = await buildApp(config, container);

app.listen({ port: config.port, host: "127.0.0.1" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});
