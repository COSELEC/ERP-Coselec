<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SidebarItem from "./SidebarItem.vue";
import {
  getStoredProfile,
  hasAnyRole,
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

const roles = computed(() => profile.value?.roles || []);

const canViewHr = computed(() => {
  return hasAnyRole(roles.value, ["Admin", "Direction", "RH / Comptabilité"]);
});

const canViewStock = computed(() => {
  return hasAnyRole(roles.value, ["Admin", "Achats", "Direction"]);
});

const canViewDocuments = computed(() => {
  return hasAnyRole(roles.value, ["Admin", "Direction", "Qualité", "Employé"]);
});

const canViewTreasury = computed(() => {
  return hasAnyRole(roles.value, ["RH", "RH / Comptabilité","Admin"]);
});

const canViewProjects = computed(() => {
  return hasAnyRole(roles.value, ["Admin", "Direction", "Chef de Projet", "Chef d'Equipe", "Commercial"]);
});

const canViewAdmin = computed(() => {
  return hasAnyRole(roles.value, ["Admin"]);
});

const canViewValidationRequests = computed(() => {
  return hasAnyRole(roles.value, ["Admin", "Direction", "RH / Comptabilité", "Achats"]);
});

const canViewFuelRequests = computed(() => {
  return hasAnyRole(roles.value, ["Admin", "Direction", "Achats", "Employé"]);
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

      <!-- User Info Placeholder -->
      <div v-if="!collapsed" class="mt-8 flex flex-col space-y-1">
        <span class="text-sm text-red-200">Connecté en tant que</span>
        <span class="font-medium text-lg capitalize">{{ profile?.name || 'Utilisateur' }}</span>
        <span class="text-xs text-red-100 capitalize">{{ roles.join(', ') || 'Aucun rôle' }}</span>
        
        <router-link to="/profile" class="mt-2 text-xs flex items-center space-x-1 hover:text-white text-red-200 transition-colors w-max">
            <span class="material-symbols-outlined text-sm">person</span>
            <span>Mon Profil</span>
        </router-link>
      </div>
    </div>

    <nav class="p-4 space-y-6">
    
      <!-- Général / Commun -->
      <div>
        <h2 v-if="!collapsed" class="text-xs uppercase text-red-200 mb-2">
          Entreprise
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
      <div>
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
          icon="apartment"
          label="Départements"
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
          icon="assignment"
          label="Mes demandes"
          :collapsed="collapsed"
        />

        <SidebarItem
          v-if="canViewValidationRequests"
          to="/admin/requests"
          icon="approval"
          label="Validation Demandes"
          :collapsed="collapsed"
        />

        <SidebarItem
          v-if="canViewFuelRequests"
          to="/fuel-requests"
          icon="local_gas_station"
          label="Demandes Carburant"
          :collapsed="collapsed"
        />
      </div>

      <!-- Documents / GED -->
      <div v-if="canViewDocuments">
        <h2
          v-if="!collapsed"
          class="text-xs uppercase text-red-200 mb-2"
        >
          Documents
        </h2>

        <SidebarItem
          to="/norms"
          icon="folder_special"
          label="Bibliothèque de Normes"
          :collapsed="collapsed"
        />
      </div>

      <!-- Trésorerie -->
      <div v-if="canViewTreasury">
        <h2
          v-if="!collapsed"
          class="text-xs uppercase text-red-200 mb-2"
        >
          Trésorerie
        </h2>

        <SidebarItem
          to="/caisse"
          icon="receipt_long"
          label="Pièce de Caisse"
          :collapsed="collapsed"
        />
        
        <SidebarItem
          to="/bank-voucher"
          icon="account_balance"
          label="Pièce de Banque"
          :collapsed="collapsed"
        />
      </div>


      <!-- Stock -->
      <div v-if="canViewStock">
        <h2
          v-if="!collapsed"
          class="text-xs uppercase text-red-200 mb-2"
        >
          Stock
        </h2>

        <SidebarItem
          to="/stock"
          icon="inventory_2"
          label="Vue d'ensemble"
          :collapsed="collapsed"
        />

        <SidebarItem
          to="/stock/movement"
          icon="sync_alt"
          label="Mouvements"
          :collapsed="collapsed"
        />

        <SidebarItem
          to="/stock/canvas"
          icon="view_kanban"
          label="Canvas"
          :collapsed="collapsed"
        />

        <SidebarItem
          to="/stock-reservations"
          icon="event_seat"
          label="Réservations"
          :collapsed="collapsed"
        />

        <SidebarItem
          to="/procurement"
          icon="shopping_cart"
          label="Achats"
          :collapsed="collapsed"
        />
      </div>

      <div v-if="canViewProjects">
        <h2 v-if="!collapsed" class="text-xs uppercase text-red-200 mb-2">Projets</h2>
        <SidebarItem to="/project-dashboard" icon="dashboard" label="Dashboard Projet" :collapsed="collapsed"></SidebarItem>
        <SidebarItem to="/projects" icon="work" label="Projets" :collapsed="collapsed"></SidebarItem>
        <SidebarItem to="/portfolio" icon="pie_chart" label="Portfolio" :collapsed="collapsed"></SidebarItem>
        <SidebarItem to="/project-budget" icon="account_balance_wallet" label="Budgets" :collapsed="collapsed"></SidebarItem>
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