<script setup>
import Button from "primevue/button";
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const sections = computed(() => {
  const staff = auth.hasRole("ADMIN", "MANAGER");
  const items = [];
  if (staff) {
    items.push({
      title: "Payroll",
      links: [
        { to: "/dashboard", label: "Dashboard", icon: "pi pi-home" },
        { to: "/employees", label: "Employees", icon: "pi pi-users" },
        ...(auth.isAdmin ? [{ to: "/departments", label: "Departments", icon: "pi pi-sitemap" }] : []),
        { to: "/timesheets", label: "Timesheets", icon: "pi pi-clock" },
        { to: "/payruns", label: "Pay runs", icon: "pi pi-wallet" },
        { to: "/reports", label: "Reports", icon: "pi pi-chart-bar" },
        ...(auth.isAdmin ? [{ to: "/settings", label: "Settings", icon: "pi pi-cog" }] : []),
      ],
    });
  }
  if (auth.user?.employeeId) {
    items.push({
      title: "Me",
      links: [
        { to: "/my/payslips", label: "My payslips", icon: "pi pi-file" },
        { to: "/my/timesheets", label: "My timesheets", icon: "pi pi-calendar" },
        { to: "/my/profile", label: "Profile", icon: "pi pi-user" },
      ],
    });
  }
  return items;
});

async function logout() {
  await auth.logout();
  router.replace("/login");
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">Acme Payroll</div>
      <nav aria-label="Main navigation">
        <template v-for="s in sections" :key="s.title">
          <div class="section">{{ s.title }}</div>
          <RouterLink v-for="l in s.links" :key="l.to" :to="l.to"><i :class="l.icon" aria-hidden="true" /> {{ l.label }}</RouterLink>
        </template>
      </nav>
    </aside>
    <div class="main">
      <header class="topbar">
        <span>{{ auth.user?.name }} <span class="muted">({{ auth.role?.toLowerCase() }})</span></span>
        <Button label="Sign out" icon="pi pi-sign-out" severity="secondary" size="small" outlined data-test="logout" @click="logout" />
      </header>
      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
