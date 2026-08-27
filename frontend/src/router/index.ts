import { createRouter, createWebHistory } from "vue-router";
import {
  clearStoredProfile,
  getStoredProfile,
  hasPermission,
  refreshCurrentUserProfile,
} from "@/services/session";

import LoginView from "../views/LoginView.vue";
import HomeView from "../views/HomeView.vue";
import EmployeesView from "../views/EmployeesView.vue";
const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    component: LoginView,
  },
  {
    path: "/home",
    component: HomeView,
  },
  {
    path: "/profile",
    name: "profile",
    component: () => import("../views/ProfileView.vue"),
  },
  {
    path: "/employees",
    component: EmployeesView,
    meta: {
      requiredPermissions: ["employees.read"],
    },
  },
  {
    path: "/departments",
    component: () => import("../views/employees/DepartmentView.vue"),
    meta: {
      requiredPermissions: ["employees.read"],
    },
  },
  {
    path: "/org-chart",
    component: () => import("../views/employees/OrganizationView.vue"),
  },
  {
    path: "/stock/movement",
    component: () => import("../views/Stock/StockMovementView.vue"),
    meta: {
      requiredPermissions: ["stock.read"],
    },
  },
  {
    path: "/stock",
    component: () => import("../views/Stock/StockOverviewView.vue"),
    meta: {
      requiredPermissions: ["stock.read"],
    },
  },
  {
    path: "/stock/canvas",
    component: () => import("../views/Stock/StockCanvasView.vue"),
    meta: {
      requiredPermissions: ["stock.read"],
    },
  },
  {
    path: "/stock/matrix",
    component: () => import("../views/Stock/StockMatrixView.vue"),
    meta: {
      requiredPermissions: ["stock.read"],
    },
  },
  {
    path: "/stock/reception",
    component: () => import("../views/Stock/ReceptionControlForm.vue"),
    meta: {
      requiredPermissions: ["stock.create"],
    },
  },
  {
    path: "/stock/delivery-notes",
    component: () => import("../views/Stock/DeliveryNoteView.vue"),
    meta: {
      requiredPermissions: ["stock.read"],
    },
  },
  {
    path: "/fuel-requests",
    name: "fuel-requests",
    component: () => import("../views/requests/FuelRequestsView.vue"),
    meta: { requiredPermissions: ["fuel_requests.read"] }
  },
  {
    path: "/quality",
    name: "quality",
    component: () => import("../views/quality/QualityDashboardView.vue"),
    meta: { requiredPermissions: ["documents.read"] },
  },
  {
    path: "/quality/kpi",
    name: "quality-kpi",
    component: () => import("../views/quality/KpiDashboardView.vue"),
    meta: { requiredPermissions: ["documents.read"] },
  },
  {
    path: "/quality/library",
    name: "quality-library",
    component: () => import("../views/quality/QualityLibraryView.vue"),
  },
  {
    path: "/quality/:id",
    name: "quality-detail",
    component: () => import("../views/quality/QualityDocumentDetail.vue"),
    meta: { requiredPermissions: ["documents.read"] },
  },
  {
    path: "/requests",
    name: "requests",
    component: () => import("../views/RequestsView.vue")
  },
  {
    path: "/norms",
    name: "norms",
    component: () => import("../views/NormLibraryView.vue"),
    meta: { requiredPermissions: ["documents.read"] }
  },
  {
    path: "/caisse",
    name: "caisse",
    component: () => import("../views/CaisseView.vue"),
    meta: { requiredPermissions: ["dashboard.read"] }
  },
  {
    path: "/bank-voucher",
    name: "bank-voucher",
    component: () => import("../views/BankVoucherView.vue"),
    meta: { requiredPermissions: ["dashboard.read"] }
  },
  {
    path: "/requests/:section(hr|it|facilities)",
    name: "request-form",
    component: () => import("../views/RequestFormView.vue"),
    props: true
  },
  {
    path: "/projects",
    name: "projects",
    component: () => import("@/views/project/ProjectView.vue"),
    props: true,
    meta: { requiredPermissions: ["projects.read"] }
  },
  {
    path: "/admin/requests",
    name: "admin-requests",
    component: () => import("@/views/Admin/AdminRequestsView.vue"),
  },
  {
    path: "/admin/users",
    name: "admin-users",
    component: () => import("@/views/Admin/UsersView.vue"),
    meta: { requiredPermissions: ["users.read", "roles.read"] }
  },
  {
    path: "/project-budget",
    name: "project-budget",
    component: () => import("../views/ProjectBudgetView.vue"),
    meta: { requiredPermissions: ["projects.read"] }
  },
  {
    path: "/procurement",
    name: "procurement",
    component: () => import("../views/ProcurementView.vue"),
    meta: { requiredPermissions: ["stock.read"] }
  },
  {
    path: "/stock-reservations",
    name: "stock-reservations",
    component: () => import("../views/StockReservationView.vue"),
    meta: { requiredPermissions: ["stock.read", "projects.read"] }
  },
  {
    path: "/project-dashboard",
    name: "project-dashboard",
    component: () => import("../views/ProjectDashboardView.vue"),
    meta: { requiredPermissions: ["projects.read", "dashboard.read"] }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

async function getActiveProfile() {
  const cached = getStoredProfile();

  if (cached) {
    return cached;
  }

  try {
    return await refreshCurrentUserProfile();
  } catch {
    return null;
  }
}

router.beforeEach(async (to) => {
  const isPublicRoute = to.path === "/login";
  const profile = await getActiveProfile();

  if (isPublicRoute) {
    if (profile) {
      return "/home";
    }
    return;
  }

  if (!profile) {
    clearStoredProfile();
    return "/login";
  }

  const requiredPermissions = (to.meta.requiredPermissions as string[] | undefined) || [];

  if (requiredPermissions.length > 0) {
    const authorized = hasPermission(profile.permissions, requiredPermissions);

    if (!authorized) {
      return "/home";
    }
  }
});

export default router;