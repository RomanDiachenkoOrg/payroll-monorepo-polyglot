import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/stores/auth";

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
  });

  it("persists the session and derives the home route", () => {
    const auth = useAuthStore();
    auth.setSession("t", { id: 1, role: "EMPLOYEE", name: "Emily" });
    expect(auth.isAuthenticated).toBe(true);
    expect(auth.homeRoute).toBe("/my/payslips");
    setActivePinia(createPinia());
    expect(useAuthStore().token).toBe("t");
  });

  it("checks roles and clears the session", () => {
    const auth = useAuthStore();
    auth.setSession("t", { id: 1, role: "MANAGER" });
    expect(auth.hasRole("ADMIN", "MANAGER")).toBe(true);
    expect(auth.homeRoute).toBe("/dashboard");
    auth.clear();
    expect(auth.isAuthenticated).toBe(false);
    expect(localStorage.getItem("payroll.session")).toBeNull();
  });
});
