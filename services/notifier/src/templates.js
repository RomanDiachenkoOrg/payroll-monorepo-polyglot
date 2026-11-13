const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

function formatDate(value) {
  const d = value instanceof Date ? value : new Date(`${value}T00:00:00Z`);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
}

/** Email sent to each employee when a pay run is approved. */
export function payslipReadyEmail({ firstName, periodStart, periodEnd, payDate, net, payslipId }, portalUrl) {
  return {
    subject: `Your payslip for ${formatDate(periodStart)} - ${formatDate(periodEnd)} is ready`,
    body: [
      `Hi ${firstName},`,
      "",
      `Your payslip for the period ${formatDate(periodStart)} to ${formatDate(periodEnd)} is now available.`,
      `Net pay of ${usd.format(Number(net))} will be paid on ${formatDate(payDate)}.`,
      "",
      `View it online: ${portalUrl}/payslips/${payslipId}`,
      "",
      "Acme Payroll",
    ].join("\n"),
  };
}

/** Email sent to an employee when a manager rejects a timesheet. */
export function timesheetRejectedEmail({ firstName, weekStart, reason, decidedBy }, portalUrl) {
  return {
    subject: `Timesheet for the week of ${formatDate(weekStart)} was returned`,
    body: [
      `Hi ${firstName},`,
      "",
      `${decidedBy ?? "Your manager"} returned your timesheet for the week of ${formatDate(weekStart)}.`,
      `Reason: ${reason}`,
      "",
      `Please correct it and submit again: ${portalUrl}/my/timesheets`,
      "",
      "Acme Payroll",
    ].join("\n"),
  };
}

export function parseEvent(raw) {
  let event;
  try {
    event = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!event || typeof event.type !== "string") return null;
  return event;
}
