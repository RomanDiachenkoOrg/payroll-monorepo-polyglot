import { createRouter, createWebHistory } from "vue-router";
import AppLayout from "@/layouts/AppLayout.vue";
import { useAuthStore } from "@/stores/auth";

const STAFF = ["ADMIN", "MANAGER"];

const routes = [
  { path: "/login", name: "login", component: () => import("@/views/LoginView.vue"), meta: { public: true } },
  {
    path: "/",
    component: AppLayout,
    children: [
      { path: "", redirect: () => useAuthStore().homeRoute },
      { path: "dashboard", name: "dashboard", component: () => import("@/views/DashboardView.vue"), meta: { roles: STAFF } },
      { path: "employees", name: "employees", component: () => import("@/views/EmployeesView.vue"), meta: { roles: STAFF } },
      { path: "employees/:id", name: "employee", component: () => import("@/views/EmployeeDetailView.vue"), meta: { roles: STAFF } },
      { path: "departments", name: "departments", component: () => import("@/views/DepartmentsView.vue"), meta: { roles: ["ADMIN"] } },
      { path: "timesheets", name: "timesheets", component: () => import("@/views/TimesheetsView.vue"), meta: { roles: STAFF } },
      { path: "payruns", name: "payruns", component: () => import("@/views/PayRunsView.vue"), meta: { roles: STAFF } },
      { path: "payruns/:id", name: "payrun", component: () => import("@/views/PayRunDetailView.vue"), meta: { roles: STAFF } },
      { path: "payslips/:id", name: "payslip", component: () => import("@/views/PayslipView.vue") },
      { path: "reports", name: "reports", component: () => import("@/views/ReportsView.vue"), meta: { roles: STAFF } },
      { path: "settings", name: "settings", component: () => import("@/views/SettingsView.vue"), meta: { roles: ["ADMIN"] } },
      { path: "my/payslips", name: "my-payslips", component: () => import("@/views/MyPayslipsView.vue") },
      { path: "my/timesheets", name: "my-timesheets", component: () => import("@/views/MyTimesheetsView.vue") },
      { path: "my/profile", name: "profile", component: () => import("@/views/ProfileView.vue") },
      { path: ":pathMatch(.*)*", name: "not-found", component: () => import("@/views/NotFoundView.vue") },
    ],
  },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.public) {
    return auth.isAuthenticated && to.name === "login" ? auth.homeRoute : true;
  }
  if (!auth.isAuthenticated) return { name: "login", query: { redirect: to.fullPath } };
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) return auth.homeRoute;
  return true;
});

export default router;
