<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import api from "@/services/api";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import { Bar } from 'vue-chartjs'
import { useToast } from '@/composables/useToast'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)
const toast = useToast()

const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const loading = ref(true);
const hrStats = ref<any>(null);

const kpis = ref([
  { title: "Progression Globale", value: "0%", color: "text-purple-600", bg: "bg-purple-50" },
  { title: "Jalons Terminés", value: "0/0", color: "text-green-600", bg: "bg-green-50" },
  { title: "Budget Consommé", value: "0%", color: "text-blue-600", bg: "bg-blue-50" },
  { title: "Tâches Ouvertes", value: "0", color: "text-red-600", bg: "bg-red-50" },
]);

const chartData = ref({
  labels: [] as string[],
  datasets: [
    {
      label: 'Dépenses (FCFA)',
      backgroundColor: '#d10f2f',
      data: [] as number[]
    }
  ]
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false
};

const fetchProjects = async () => {
  try {
    const res = await api.get('/projects/');
    projects.value = res.data;
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id;
      await fetchDashboardData();
    } else {
      loading.value = false;
    }
  } catch {
    loading.value = false;
  }
};

const fetchDashboardData = async () => {
  if (!selectedProjectId.value) return;
  loading.value = true;
  try {
    const res = await api.get(`/projects/${selectedProjectId.value}/dashboard`);
    kpis.value = res.data.kpis;
    chartData.value = {
      labels: res.data.financial_chart.labels,
      datasets: [
        {
          label: 'Dépenses (FCFA)',
          backgroundColor: '#d10f2f',
          data: res.data.financial_chart.data
        }
      ]
    };
    hrStats.value = res.data.hr_stats;
  } catch {
  } finally {
    loading.value = false;
  }
};

watch(selectedProjectId, () => {
  fetchDashboardData();
});

onMounted(() => {
  fetchProjects();
});

const downloadProjectReport = async () => {
  if (!selectedProjectId.value) return;
  try {
    toast.success("Génération du rapport en cours...");
    const res = await api.get(`/projects/${selectedProjectId.value}/download-report`);
    if (res.data && res.data.pdf_url) {
      window.open(res.data.pdf_url, '_blank');
    }
  } catch (err: any) {
    toast.error("Erreur lors de la génération du rapport.");
  }
};
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-8 w-full">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Dashboard Projet</h1>
          <p class="mt-1 text-gray-500">Suivi des KPIs, Budget et Avancement du Projet</p>
        </div>
        <div class="flex gap-4 items-center">
          <select v-model="selectedProjectId" class="border border-gray-300 rounded-lg px-4 py-2 bg-white min-w-[250px] shadow-sm">
            <option v-for="p in projects" :key="p.id" :value="p.id">[{{ p.code }}] {{ p.nom }}</option>
          </select>
          <button @click="downloadProjectReport" :disabled="!selectedProjectId" class="bg-[#d10f2f] hover:bg-[#97091f] disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
            <span class="material-symbols-outlined text-sm">download</span>
            Exporter Rapport
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
      </div>

      <div v-else-if="!selectedProjectId" class="text-center py-12 text-gray-500">Aucun projet disponible.</div>

      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="kpi in kpis" :key="kpi.title" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div :class="[kpi.bg, kpi.color, 'w-12 h-12 rounded-lg flex items-center justify-center mb-4']">
              <span class="material-symbols-outlined">analytics</span>
            </div>
            <p class="text-sm font-medium text-gray-500">{{ kpi.title }}</p>
            <p class="text-2xl font-bold text-gray-900 mt-1">{{ kpi.value }}</p>
          </div>
        </div>
        
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-lg font-bold text-gray-900 mb-4">Dépenses Financières Annuelles</h2>
          <div class="h-80 w-full">
            <Bar :data="chartData" :options="chartOptions" />
          </div>
        </div>
        
        <!-- HR Stats Section -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6" v-if="hrStats">
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-[#d10f2f]">group</span>
              Ressources Humaines Actives
            </h2>
            <div class="space-y-4">
              <div class="flex justify-between items-center border-b border-gray-100 pb-3">
                <span class="text-gray-500 font-medium">Employés affectés</span>
                <span class="font-bold text-gray-900 text-lg">{{ hrStats.num_assigned_employees }}</span>
              </div>
              <div class="flex justify-between items-center border-b border-gray-100 pb-3">
                <span class="text-gray-500 font-medium">Allocation moyenne</span>
                <span class="font-bold text-[#d10f2f] text-lg">{{ hrStats.average_allocation }}%</span>
              </div>
            </div>
          </div>
          
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-[#d10f2f]">work</span>
              Distribution par Rôle
            </h2>
            <div class="space-y-3 max-h-48 overflow-y-auto pr-2">
              <div v-for="(count, role) in hrStats.role_distribution" :key="role" class="flex justify-between items-center bg-gray-50 p-3 rounded-lg border border-gray-100">
                <span class="text-gray-700 font-medium">{{ role }}</span>
                <span class="bg-[#d10f2f] text-white w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold">{{ count }}</span>
              </div>
              <div v-if="Object.keys(hrStats.role_distribution || {}).length === 0" class="text-gray-400 text-sm italic text-center py-4">
                Aucune donnée de ressource humaine.
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </AppLayout>
</template>
