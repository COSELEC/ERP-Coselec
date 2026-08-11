import { createRouter, createWebHistory } from "vue-router";
import {
  clearStoredProfile,
  getStoredProfile,
  hasAnyRole,
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
      requiredRoles: ["Admin", "Direction", "RH / Comptabilité"],
    },
  },
  {
    path: "/departments",
    component: () => import("../views/employees/DepartmentView.vue"),
    meta: {
      requiredRoles: ["Admin", "Direction", "RH / Comptabilité"],
    },
  },
  {
    path: "/org-chart",
    component: () => import("../views/employees/OrganizationView.vue"),
  },
  {
    path: "/attendance",
    name: "attendance",
    component: () => import("../views/employees/AttendanceView.vue"),
    meta: {
      requiredRoles: ["Admin", "Direction", "RH / Comptabilité"],
    },
  },
  {
    path: "/stock/movement",
    component: () => import("../views/Stock/StockMovementView.vue"),
    meta: {
      requiredRoles: ["Admin", "Achats", "Direction"],
    },
  },
  {
    path: "/stock",
    component: () => import("../views/Stock/StockOverviewView.vue"),
    meta: {
      requiredRoles: ["Admin", "Achats", "Direction"],
    },
  },
  {
    path: "/stock/canvas",
    component: () => import("../views/Stock/StockCanvasView.vue"),
    meta: {
      requiredRoles: ["Admin", "Achats", "Direction"],
    },
  },
  {
    path: "/stock/matrix",
    component: () => import("../views/Stock/StockMatrixView.vue"),
    meta: {
      requiredRoles: ["Admin", "Achats", "Direction"],
    },
  },
  {
    path: "/stock/reception",
    component: () => import("../views/Stock/ReceptionControlForm.vue"),
    meta: {
      requiredRoles: ["Admin", "Achats", "Direction"],
    },
  },
  {
    path: "/stock/delivery-notes",
    component: () => import("../views/Stock/DeliveryNoteView.vue"),
    meta: {
      requiredRoles: ["Admin", "Stock / Logistique", "Chef de Projet", "Direction"],
    },
  },

  {
    path: "/fuel-requests",
    name: "fuel-requests",
    component: () => import("../views/requests/FuelRequestsView.vue"),
    meta: { requiredRoles: ["Admin", "Achats", "Direction"] }
  },

  {
    path: "/quality",
    name: "quality",
    component: () => import("../views/quality/QualityDashboardView.vue"),
    meta: { requiredRoles: ["Admin", "Direction", "Qualité"] },
  },
  {
    path: "/quality/kpi",
    name: "quality-kpi",
    component: () => import("../views/quality/KpiDashboardView.vue"),
    meta: { requiredRoles: ["Admin", "Direction", "Qualité"] },
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
    meta: { requiredRoles: ["Admin", "Direction", "Qualité"] },
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
    meta: { requiredRoles: ["Admin", "Direction", "Qualité"] }
  },
  {
    path: "/caisse",
    name: "caisse",
    component: () => import("../views/CaisseView.vue"),
    meta: { requiredRoles: ["RH", "RH / Comptabilité", "Admin"] }
  },
  {
    path: "/bank-voucher",
    name: "bank-voucher",
    component: () => import("../views/BankVoucherView.vue"),
    meta: { requiredRoles: ["RH", "RH / Comptabilité", "Admin"] }
  }
  ,
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
    meta: { requiredRoles: ["Admin", "Direction", "Chef de Projet", "Chef d'Equipe", "Commercial"] }
  },
  {
    path: "/admin/requests",
    name: "admin-requests",
    component: () => import("@/views/Admin/AdminRequestsView.vue"),
    meta: { requiredRoles: ["Admin", "RH", "Direction", "IT Admin", "Admin IT", "IT", "Responsable IT", "Facility Manager", "Facility", "Finance", "Stock / Logistique"] }
  },
  {
    path: "/admin/users",
    name: "admin-users",
    component: () => import("@/views/Admin/UsersView.vue"),
    meta: { requiredRoles: ["Admin"] }
  },
  {
    path: "/portfolio",
    name: "portfolio",
    component: () => import("../views/PortfolioView.vue"),
    meta: { requiredRoles: ["Admin", "Direction", "Finance", "Responsable Projet"] }
  },
  {
    path: "/project-budget",
    name: "project-budget",
    component: () => import("../views/ProjectBudgetView.vue"),
    meta: { requiredRoles: ["Admin", "Direction", "Finance", "Responsable Projet"] }
  },
  {
    path: "/procurement",
    name: "procurement",
    component: () => import("../views/ProcurementView.vue"),
    meta: { requiredRoles: ["Admin", "Commercial", "Achat", "Finance", "Responsable Projet", "Direction"] }
  },
  {
    path: "/stock-reservations",
    name: "stock-reservations",
    component: () => import("../views/StockReservationView.vue"),
    meta: { requiredRoles: ["Admin", "Stock / Logistique", "Responsable Projet", "Direction", "Achat"] }
  },
  {
    path: "/project-dashboard",
    name: "project-dashboard",
    component: () => import("../views/ProjectDashboardView.vue"),
    meta: { requiredRoles: ["Admin", "Responsable Projet", "Direction", "Stock / Logistique", "Achat", "Finance"] }
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

  const requiredRoles = (to.meta.requiredRoles as string[] | undefined) || [];

  if (requiredRoles.length > 0) {
    const authorized = hasAnyRole(profile.roles, requiredRoles);

    if (!authorized) {
      return "/home";
    }
  }
});


export default router;