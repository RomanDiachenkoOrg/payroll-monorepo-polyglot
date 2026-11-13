import { describe, expect, it } from "vitest";
import { validateDepartment, validateEmployee, validateHours, validateLogin } from "@/utils/validation";

const valid = {
  firstName: "Ada",
  lastName: "Lovelace",
  email: "ada@acme.test",
  title: "Engineer",
  departmentId: 1,
  payType: "SALARIED",
  annualSalary: 50000,
  hireDate: "2024-01-01",
};

describe("validation", () => {
  it("validates login", () => {
    expect(validateLogin({ email: "", password: "" })).toEqual({ email: "Email is required", password: "Password is required" });
    expect(validateLogin({ email: "x@y.z", password: "p" })).toEqual({});
  });

  it("accepts a valid employee", () => {
    expect(validateEmployee(valid, "2026-01-01")).toEqual({});
  });

  it("rejects bad employee data", () => {
    const errors = validateEmployee({ ...valid, email: "nope", annualSalary: 0, hireDate: "2027-01-01" }, "2026-01-01");
    expect(Object.keys(errors).sort()).toEqual(["annualSalary", "email", "hireDate"]);
  });

  it("checks hourly rate for hourly staff", () => {
    expect(validateEmployee({ ...valid, payType: "HOURLY", hourlyRate: null }, "2026-01-01").hourlyRate).toBeDefined();
  });

  it("validates timesheet hours", () => {
    expect(validateHours([8, 8, 8, 8, 8, 0, 0])).toBeNull();
    expect(validateHours([25, 0, 0, 0, 0, 0, 0])).toMatch(/between 0 and 24/);
    expect(validateHours([8, 8])).toMatch(/7 days/);
  });

  it("validates departments", () => {
    expect(validateDepartment({ name: "R", code: "R1" })).toHaveProperty("code");
  });
});
