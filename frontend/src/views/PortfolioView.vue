<script setup lang="ts">
import { ref, onMounted } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import PortfolioMap from "@/components/project/PortfolioMap.vue";
import api from "@/services/api";

const kpis = ref({
  total_projects: 0,
  ongoing_projects: 0,
  completed_projects: 0,
  pending_projects: 0,
  total_budget_allocated: 0,
  total_budget_consumed: 0,
  budget_consumption_rate: 0
});

const projects = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const [kpisRes, projectsRes] = await Promise.all([
      api.get('/portfolio/kpis'),
      api.get('/projects/')
    ]);
    
    kpis.value = kpisRes.data;
    projects.value = projectsRes.data;
  } catch {
    error.value = "Erreur lors du chargement des données du portfolio.";
  } finally {
    loading.value = false;
  }
});

const getStatusColor = (status: string) => {
  switch(status) {
    case 'En cours': return 'bg-blue-100 text-blue-800';
    case 'Approuvé': return 'bg-green-100 text-green-800';
    case 'Terminé': return 'bg-gray-100 text-gray-800';
    case 'Annulé': return 'bg-red-100 text-red-800';
    default: return 'bg-yellow-100 text-yellow-800';
  }
};

const getConsumptionRate = (project: any) => {
  if (!project.budget_estime || project.budget_estime === 0) return 0;
  return Math.min(100, Math.round((project.budget_consumed / project.budget_estime) * 100));
};

</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-8 w-full">
      
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Portfolio Projets</h1>
          <p class="mt-1 text-gray-500">Vue globale sur tous les projets et leur santé financière</p>
        </div>
        <button disabled class="bg-gray-300 text-gray-500 px-4 py-2 rounded-lg flex items-center gap-2 cursor-not-allowed" title="Bientôt disponible">
          <span class="material-symbols-outlined text-sm">print</span>
          Exporter
        </button>
      </div>

      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
      </div>

      <div v-else-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg">
        {{ error }}
      </div>

      <template v-else>
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <p class="text-sm font-medium text-gray-500">Total Projets</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ kpis.total_projects }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <p class="text-sm font-medium text-gray-500">Projets en cours</p>
            <p class="text-3xl font-bold text-blue-600 mt-2">{{ kpis.ongoing_projects }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <p class="text-sm font-medium text-gray-500">Projets en attente</p>
            <p class="text-3xl font-bold text-amber-500 mt-2">{{ kpis.pending_projects }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <p class="text-sm font-medium text-gray-500">Projets terminés</p>
            <p class="text-3xl font-bold text-green-600 mt-2">{{ kpis.completed_projects }}</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <p class="text-sm font-medium text-gray-500">Budget Consommé</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ (kpis.total_budget_consumed / 1000000).toFixed(1) }}M / {{ (kpis.total_budget_allocated / 1000000).toFixed(1) }}M</p>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <p class="text-sm font-medium text-gray-500">Taux de Consommation</p>
            <div class="flex items-end gap-2 mt-2">
              <p class="text-3xl font-bold text-red-600">{{ kpis.budget_consumption_rate }}%</p>
            </div>
          </div>
        </div>

        <!-- Global Interactive Map -->
        <PortfolioMap :projects="projects" />

        <!-- Project Cards Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div v-for="project in projects" :key="project.id" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div class="flex justify-between items-start mb-4">
              <div>
                <h3 class="text-lg font-bold text-gray-900">{{ project.nom }}</h3>
                <p class="text-sm text-gray-500">Client: {{ project.client_name || 'Non assigné' }}</p>
              </div>
              <span :class="getStatusColor(project.status)" class="px-3 py-1 rounded-full text-xs font-semibold uppercase">{{ project.status }}</span>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="font-medium text-gray-700">Consommation Budget</span>
                  <span class="font-bold text-red-600">{{ getConsumptionRate(project) }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-red-500 h-2 rounded-full" :style="{ width: getConsumptionRate(project) + '%' }"></div>
                </div>
              </div>
              
              <div class="flex gap-4 pt-4 border-t border-gray-50">
                <div class="flex-1">
                  <p class="text-xs text-gray-500 uppercase">Ressources</p>
                  <p class="font-bold text-gray-900">{{ project.employees_count }} Employé{{ project.employees_count > 1 ? 's' : '' }}</p>
                </div>
                <div class="flex-1">
                  <p class="text-xs text-gray-500 uppercase">Phase Actuelle</p>
                  <p class="font-bold text-gray-900">{{ project.current_phase || 'Non défini' }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="projects.length === 0" class="col-span-1 lg:col-span-2 bg-white rounded-xl border border-gray-100 p-12 text-center text-gray-500">
            Aucun projet trouvé.
          </div>
        </div>
      </template>

    </div>
  </AppLayout>
</template>
