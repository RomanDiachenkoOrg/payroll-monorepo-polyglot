import { describe, expect, it } from "vitest";
import { addDays, mondayOf, money, monthRange, period, statusSeverity } from "@/utils/format";

describe("format helpers", () => {
  it("formats money as USD", () => {
    expect(money(1234.5)).toBe("$1,234.50");
    expect(money(null)).toBe("-");
  });

  it("formats a period", () => {
    expect(period("2026-10-01", "2026-10-31")).toBe("Oct 1, 2026 - Oct 31, 2026");
  });

  it("finds the monday of a week", () => {
    expect(mondayOf(new Date(2026, 10, 13))).toBe("2026-11-09");
    expect(addDays("2026-11-09", 6)).toBe("2026-11-15");
  });

  it("computes month ranges", () => {
    expect(monthRange(-1, new Date(2026, 2, 15))).toEqual({ start: "2026-02-01", end: "2026-02-28" });
  });

  it("maps statuses to tag severities", () => {
    expect(statusSeverity("REJECTED")).toBe("danger");
    expect(statusSeverity("UNKNOWN")).toBe("secondary");
  });
});
