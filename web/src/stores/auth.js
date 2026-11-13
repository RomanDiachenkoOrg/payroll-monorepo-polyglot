import { defineStore } from "pinia";

const KEY = "payroll.session";

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? { token: null, user: null };
  } catch {
    return { token: null, user: null };
  }
}

export const useAuthStore = defineStore("auth", {
  state: () => load(),
  getters: {
    isAuthenticated: (s) => !!s.token,
    role: (s) => s.user?.role ?? null,
    isAdmin: (s) => s.user?.role === "ADMIN",
    isManager: (s) => s.user?.role === "MANAGER",
    homeRoute: (s) => (s.user?.role === "EMPLOYEE" ? "/my/payslips" : "/dashboard"),
  },
  actions: {
    hasRole(...roles) {
      return !!this.user && roles.includes(this.user.role);
    },
    setSession(token, user) {
      this.token = token;
      this.user = user;
      localStorage.setItem(KEY, JSON.stringify({ token, user }));
    },
    async login(email, password) {
      const { http } = await import("@/api/http");
      const res = await http.post("/api/auth/login", { email, password });
      this.setSession(res.token, res.user);
      return res.user;
    },
    async logout() {
      const { http } = await import("@/api/http");
      try {
        await http.post("/api/auth/logout");
      } catch {
        // session may already be gone
      }
      this.clear();
    },
    clear() {
      this.token = null;
      this.user = null;
      localStorage.removeItem(KEY);
    },
  },
});
