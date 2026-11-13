import pg from "pg";
import { createClient } from "redis";
import { config } from "./config.js";
import { createHandlers } from "./handlers.js";
import { parseEvent } from "./templates.js";

const db = new pg.Pool({ connectionString: config.databaseUrl, max: 4 });
const redis = createClient({ url: config.redisUrl });
redis.on("error", (err) => console.error("[redis]", err.message));

const handlers = createHandlers(db, { portalUrl: config.portalUrl });
let running = true;

async function processMessage(raw) {
  const event = parseEvent(raw);
  if (!event) {
    console.warn("[notifier] skipping malformed message", raw);
    return;
  }
  const handler = handlers[event.type];
  if (!handler) {
    console.info(`[notifier] no handler for ${event.type}`);
    return;
  }
  try {
    const sent = await handler(event);
    console.info(`[notifier] ${event.type} handled, ${sent} message(s) written`);
  } catch (err) {
    console.error(`[notifier] failed to handle ${event.type}:`, err.message);
  }
}

async function main() {
  await redis.connect();
  console.info(`[notifier] waiting for events on ${config.queue}`);
  while (running) {
    const item = await redis.blPop(config.queue, 5);
    if (item) await processMessage(item.element);
  }
}

async function shutdown() {
  running = false;
  await redis.quit().catch(() => undefined);
  await db.end().catch(() => undefined);
  process.exit(0);
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

main().catch((err) => {
  console.error("[notifier] fatal", err);
  process.exit(1);
});
