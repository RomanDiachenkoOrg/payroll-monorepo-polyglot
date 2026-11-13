export const config = {
  redisUrl: process.env.REDIS_URL ?? "redis://localhost:6379/0",
  databaseUrl: process.env.DATABASE_URL ?? "postgres://payroll:payroll@localhost:5432/payroll",
  queue: process.env.EVENTS_QUEUE ?? "payroll:events",
  portalUrl: process.env.PORTAL_URL ?? "http://localhost:8080",
  fromAddress: process.env.MAIL_FROM ?? "payroll@acme.test",
};
