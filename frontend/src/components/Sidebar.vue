<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SidebarItem from "./SidebarItem.vue";
import {
  getStoredProfile,
  hasPermission,
  refreshCurrentUserProfile,
  type CurrentUserProfile,
} from "@/services/session";

const collapsed = ref(false);
const profile = ref<CurrentUserProfile | null>(getStoredProfile());
const sidebarRef = ref<HTMLElement | null>(null);

const toggleSidebar = () => {
  collapsed.value = !collapsed.value;
};

const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement;
  sessionStorage.setItem("sidebarScrollPos", target.scrollTop.toString());
};

const permissions = computed(() => profile.value?.permissions || []);

const canViewHr = computed(() => {
  return hasPermission(permissions.value, ["employees.read"]);
});

const canViewStock = computed(() => {
  return hasPermission(permissions.value, ["stock.read"]);
});

const canViewDocuments = computed(() => {
  return hasPermission(permissions.value, ["documents.read"]);
});

const canViewTreasury = computed(() => {
  return hasPermission(permissions.value, ["dashboard.read", "requests.validate_finance"]);
});

const canViewProjects = computed(() => {
  return hasPermission(permissions.value, ["projects.read"]);
});

const canViewAdmin = computed(() => {
  return hasPermission(permissions.value, ["users.read", "roles.read"]);
});

const canViewValidationRequests = computed(() => {
  return hasPermission(permissions.value, ["requests.validate_hr", "requests.validate_it", "requests.validate_facility", "requests.validate_finance"]);
});

const canViewFuelRequests = computed(() => {
  return hasPermission(permissions.value, ["fuel_requests.read"]);
});

onMounted(async () => {
  if (sidebarRef.value) {
    const savedPos = sessionStorage.getItem("sidebarScrollPos");
    if (savedPos) {
      sidebarRef.value.scrollTop = parseInt(savedPos, 10);
    }
  }
  try {
    profile.value = await refreshCurrentUserProfile();
  } catch {
    profile.value = getStoredProfile();
  }
});
</script>

<template>
  <aside
    ref="sidebarRef"
    @scroll="handleScroll"
    :class="[
      collapsed ? 'w-20' : 'w-72',
      'sidebar h-screen overflow-y-auto bg-gradient-to-b from-[#d10f2f] to-[#97091f] text-white flex-shrink-0 transition-all duration-300'
    ]"
  >
    <!-- Header -->
    <div class="p-6 border-b border-white/10">
      <div class="flex items-center justify-between">
        <h1
          v-if="!collapsed"
          class="text-2xl font-bold whitespace-nowrap"
        >
          COSELEC ERP
        </h1>

        <div
          v-else
          class="w-full flex justify-center text-2xl font-bold"
        >
          C
        </div>

        <button
          @click="toggleSidebar"
          class="p-2 rounded-lg hover:bg-white/10 transition"
        >
          <span class="material-symbols-outlined">
            menu
          </span>
        </button>
      </div>
    </div>

    <nav class="p-4 space-y-6">
    
      <!-- Général / Commun -->
      <div>
        <h2 v-if="!collapsed" class="text-xs uppercase text-red-200 mb-2">
          Accueil
        </h2>
        <SidebarItem
          to="/"
          icon="dashboard"
          label="Tableau de bord"
          :collapsed="collapsed"
        />
        <SidebarItem
          to="/org-chart"
          icon="account_tree"
          label="Organigramme"
          :collapsed="collapsed"
        />
      </div>

      <!-- Qualité -->
      <div v-if="canViewDocuments">
        <h2 v-if="!collapsed" class="text-xs uppercase text-red-200 mb-2">
          Qualité
        </h2>
        <SidebarItem
          to="/quality"
          icon="verified"
          label="Documents Qualité"
          :collapsed="collapsed"
        />
        <SidebarItem
          to="/quality/kpi"
          icon="insights"
          label="KPI Qualité"
          :collapsed="collapsed"
        />
        <SidebarItem
          to="/quality/library"
          icon="local_library"
          label="Bibliothèque Qualité"
          :collapsed="collapsed"
        />
      </div>
     
      <!-- RH -->
      <div v-if="canViewHr">
        <h2
          v-if="!collapsed"
          class="text-xs uppercase text-red-200 mb-2"
        >
          Ressources Humaines
        </h2>

        <SidebarItem
          to="/employees"
          icon="people"
          label="Employés"
          :collapsed="collapsed"
        />

        <SidebarItem
          to="/departments"
          icon="calendar_month"
          label="Planning / Affectations"
          :collapsed="collapsed"
        />

      </div>

      <!-- Demandes -->
      <div>
        <h2
          v-if="!collapsed"
          class="text-xs uppercase text-red-200 mb-2"
        >
          Demandes
        </h2>

        <SidebarItem
          to="/requests"
          icon="add_circle"
          label="Mes demandes"
          :collapsed="collapsed"
        />

        <SidebarItem
          v-if="canViewValidationRequests"
          to="/admin/requests"
          icon="assignment"
          label="Toutes les demandes"
          :collapsed="collapsed"
        />
      </div>



      <!-- Admin -->
      <div v-if="canViewAdmin">
        <h2
          v-if="!collapsed"
          class="text-xs uppercase text-red-200 mb-2"
        >
          Admin
        </h2>

        <SidebarItem
          to="/admin/users"
          icon="admin_panel_settings"
          label="Gestion des utilisateurs"
          :collapsed="collapsed"
        />
      </div>

      
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  scrollbar-width: none;
}

.sidebar::-webkit-scrollbar {
  display: none;
}
</style>