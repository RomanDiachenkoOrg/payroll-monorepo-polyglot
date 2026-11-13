import { payslipReadyEmail, timesheetRejectedEmail } from "./templates.js";

const PAYSLIPS_SQL = `
  SELECT p.id AS payslip_id, p.net, e.first_name, e.email,
         to_char(pr.period_start, 'YYYY-MM-DD') AS period_start,
         to_char(pr.period_end, 'YYYY-MM-DD') AS period_end,
         to_char(pr.pay_date, 'YYYY-MM-DD') AS pay_date
  FROM payslips p
  JOIN pay_runs pr ON pr.id = p.pay_run_id
  JOIN employees e ON e.id = p.employee_id
  WHERE p.pay_run_id = $1
  ORDER BY e.last_name`;

const TIMESHEET_SQL = `
  SELECT e.first_name, e.email, to_char(t.week_start, 'YYYY-MM-DD') AS week_start,
         t.reject_reason, u.full_name AS decided_by
  FROM timesheets t
  JOIN employees e ON e.id = t.employee_id
  LEFT JOIN users u ON u.id = t.decided_by_id
  WHERE t.id = $1`;

const INSERT_SQL = `
  INSERT INTO mailbox (recipient, subject, body, event_type, related_id)
  VALUES ($1, $2, $3, $4, $5)`;

export function createHandlers(db, { portalUrl, log = console }) {
  async function deliver(recipient, mail, eventType, relatedId) {
    await db.query(INSERT_SQL, [recipient, mail.subject, mail.body, eventType, relatedId]);
    log.info(`[mail] to=${recipient} subject="${mail.subject}"`);
  }

  return {
    async "payrun.approved"(event) {
      const { rows } = await db.query(PAYSLIPS_SQL, [event.payRunId]);
      for (const r of rows) {
        const mail = payslipReadyEmail(
          {
            firstName: r.first_name,
            periodStart: r.period_start,
            periodEnd: r.period_end,
            payDate: r.pay_date,
            net: r.net,
            payslipId: r.payslip_id,
          },
          portalUrl,
        );
        await deliver(r.email, mail, "payrun.approved", event.payRunId);
      }
      return rows.length;
    },

    async "timesheet.rejected"(event) {
      const { rows } = await db.query(TIMESHEET_SQL, [event.timesheetId]);
      if (!rows.length) return 0;
      const r = rows[0];
      const mail = timesheetRejectedEmail(
        { firstName: r.first_name, weekStart: r.week_start, reason: r.reject_reason, decidedBy: r.decided_by },
        portalUrl,
      );
      await deliver(r.email, mail, "timesheet.rejected", event.timesheetId);
      return 1;
    },
  };
}
