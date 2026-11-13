import assert from "node:assert/strict";
import { test } from "node:test";
import { createHandlers } from "../src/handlers.js";
import { parseEvent, payslipReadyEmail, timesheetRejectedEmail } from "../src/templates.js";

test("payslip email contains period, amount and link", () => {
  const mail = payslipReadyEmail(
    { firstName: "Emily", periodStart: "2026-10-01", periodEnd: "2026-10-31", payDate: "2026-10-31", net: "4212.5", payslipId: 7 },
    "http://localhost:8080",
  );
  assert.match(mail.subject, /October 1, 2026 - October 31, 2026/);
  assert.match(mail.body, /\$4,212\.50/);
  assert.match(mail.body, /http:\/\/localhost:8080\/payslips\/7/);
});

test("rejected timesheet email includes the reason", () => {
  const mail = timesheetRejectedEmail({ firstName: "Kevin", weekStart: "2026-11-02", reason: "Missing ticket", decidedBy: "Michael Brooks" }, "http://x");
  assert.match(mail.body, /Reason: Missing ticket/);
  assert.match(mail.body, /Michael Brooks returned/);
});

test("parseEvent ignores malformed messages", () => {
  assert.equal(parseEvent("not json"), null);
  assert.equal(parseEvent("{}"), null);
  assert.deepEqual(parseEvent('{"type":"payrun.approved","payRunId":3}'), { type: "payrun.approved", payRunId: 3 });
});

test("payrun.approved writes one mailbox row per payslip", async () => {
  const queries = [];
  const db = {
    async query(sql, params) {
      queries.push({ sql, params });
      if (sql.includes("FROM payslips")) {
        return {
          rows: [
            { payslip_id: 1, net: "100", first_name: "A", email: "a@acme.test", period_start: "2026-10-01", period_end: "2026-10-31", pay_date: "2026-10-31" },
            { payslip_id: 2, net: "200", first_name: "B", email: "b@acme.test", period_start: "2026-10-01", period_end: "2026-10-31", pay_date: "2026-10-31" },
          ],
        };
      }
      return { rows: [] };
    },
  };
  const handlers = createHandlers(db, { portalUrl: "http://x", log: { info() {} } });
  const sent = await handlers["payrun.approved"]({ payRunId: 9 });
  assert.equal(sent, 2);
  const inserts = queries.filter((q) => q.sql.includes("INSERT INTO mailbox"));
  assert.equal(inserts.length, 2);
  assert.equal(inserts[0].params[0], "a@acme.test");
});
