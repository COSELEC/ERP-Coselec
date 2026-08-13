<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import ExcelImportModal from "@/components/ExcelImportModal.vue";
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
import 'leaflet/dist/leaflet.css';
import { LMap, LTileLayer, LMarker } from '@vue-leaflet/vue-leaflet';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)
const toast = useToast()

const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const loading = ref(true);
const hrStats = ref<any>(null);
const financials = ref<{ budgets: any[], payment_milestones: any[] }>({ budgets: [], payment_milestones: [] });
const isImportModalOpen = ref(false);
const selectedMilestonePartner = ref<string>('all');

const groupedBudgets = computed(() => {
  const groups: Record<string, any[]> = {};
  financials.value.budgets.forEach(b => {
    if (!groups[b.partner_name]) groups[b.partner_name] = [];
    groups[b.partner_name].push(b);
  });
  return groups;
});

const groupedMilestones = computed(() => {
  const groups: Record<string, any[]> = {};
  financials.value.payment_milestones.forEach(m => {
    if (!groups[m.partner_name]) groups[m.partner_name] = [];
    groups[m.partner_name].push(m);
  });
  // Sort milestones by date for each partner
  for (const p in groups) {
    groups[p].sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime());
  }
  return groups;
});

const activeProject = computed(() => {
  if (!selectedProjectId.value) return null;
  return projects.value.find(p => p.id === selectedProjectId.value);
});

const mapZoom = ref(13);

const filteredGroupedMilestones = computed(() => {
  if (selectedMilestonePartner.value === 'all') {
    return groupedMilestones.value;
  }
  const result: Record<string, any[]> = {};
  if (groupedMilestones.value[selectedMilestonePartner.value]) {
    result[selectedMilestonePartner.value] = groupedMilestones.value[selectedMilestonePartner.value];
  }
  return result;
});

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
    
    // Fetch financials
    const finRes = await api.get(`/projects/${selectedProjectId.value}/financials`);
    financials.value = finRes.data;
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

const exportGantt = async () => {
  if (!selectedProjectId.value) return;
  try {
    toast.success("Génération du Gantt en cours...");
    const res = await api.get(`/projects/${selectedProjectId.value}/export-gantt`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Gantt_${activeProject.value?.code || selectedProjectId.value}.xlsx`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    toast.error("Erreur lors de l'export du Gantt.");
    console.error('Erreur lors de l\'export', error);
  }
};

const handleImportExcel = async (file: File) => {
  if (!selectedProjectId.value) return;
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const res = await api.post(`/projects/${selectedProjectId.value}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    toast.success(res.data.message || "Importation réussie");
    await fetchDashboardData(); // Rafraîchir les données
  } catch (err: any) {
    toast.error(err.response?.data?.detail || "Erreur lors de l'importation");
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
          <button @click="isImportModalOpen = true" :disabled="!selectedProjectId" class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
            <span class="material-symbols-outlined text-sm">upload_file</span>
            Importer
          </button>
          <button @click="downloadProjectReport" :disabled="!selectedProjectId" class="bg-[#d10f2f] hover:bg-[#97091f] disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
            <span class="material-symbols-outlined text-sm">download</span>
            Exporter Rapport
          </button>
          <button @click="exportGantt" :disabled="!selectedProjectId" class="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
            <span class="material-symbols-outlined text-sm">event_note</span>
            Exporter Gantt
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
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4">Dépenses Financières Annuelles</h2>
            <div class="h-80 w-full">
              <Bar :data="chartData" :options="chartOptions" />
            </div>
          </div>
          
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-[#d10f2f]">location_on</span>
              Localisation du Projet
            </h2>
            <div class="h-80 w-full rounded-xl border border-gray-200 overflow-hidden relative z-0">
              <l-map
                v-if="activeProject && activeProject.latitude && activeProject.longitude"
                v-model:zoom="mapZoom"
                :center="[activeProject.latitude, activeProject.longitude]"
              >
                <l-tile-layer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  layer-type="base"
                  name="OpenStreetMap"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                ></l-tile-layer>
                <l-marker
                  :lat-lng="[activeProject.latitude, activeProject.longitude]"
                ></l-marker>
              </l-map>
              <div v-else class="flex flex-col items-center justify-center h-full text-gray-500 bg-gray-50 px-4 text-center">
                <span class="material-symbols-outlined text-4xl mb-2 text-gray-400">location_off</span>
                <p>Aucune localisation définie pour ce projet.</p>
              </div>
            </div>
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

        <!-- Financial Stats Section -->
        <div v-if="financials.budgets.length > 0 || financials.payment_milestones.length > 0" class="space-y-6">
          
          <h2 class="text-2xl font-bold text-gray-900 flex items-center gap-2 border-b pb-4 mt-8">
            <span class="material-symbols-outlined text-[#d10f2f]">account_balance_wallet</span>
            Finances & Prestataires
          </h2>

          <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <!-- Budgets par Prestataire -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-600">receipt_long</span>
                Budgets Alloués par Prestataire
              </h3>
              <div class="space-y-6 max-h-[500px] overflow-y-auto pr-2">
                <div v-for="(budgets, partner) in groupedBudgets" :key="partner" class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                  <h4 class="font-bold text-gray-800 mb-3 border-b pb-2">{{ partner }}</h4>
                  <div class="space-y-2">
                    <div v-for="b in budgets" :key="b.id" class="flex justify-between items-center text-sm">
                      <span class="text-gray-600">{{ b.category }}</span>
                      <span class="font-bold text-gray-900">{{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF' }).format(b.allocated_amount) }}</span>
                    </div>
                  </div>
                  <div class="mt-3 pt-2 border-t border-gray-200 flex justify-between items-center text-sm font-bold">
                    <span class="text-gray-800">Total Alloué</span>
                    <span class="text-blue-600">{{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF' }).format(budgets.reduce((sum, b) => sum + b.allocated_amount, 0)) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Échéancier de Paiement -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <span class="material-symbols-outlined text-green-600">calendar_month</span>
                  Échéancier (Décomptes)
                </h3>
                <select v-model="selectedMilestonePartner" class="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-gray-50 focus:outline-none focus:ring-1 focus:ring-green-500">
                  <option value="all">Tous les prestataires</option>
                  <option v-for="(_, partner) in groupedMilestones" :key="partner" :value="partner">{{ partner }}</option>
                </select>
              </div>
              <div class="space-y-6 max-h-[500px] overflow-y-auto pr-2">
                <div v-for="(milestones, partner) in filteredGroupedMilestones" :key="partner" class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                  <h4 class="font-bold text-gray-800 mb-3 border-b pb-2">{{ partner }}</h4>
                  <div class="relative border-l-2 border-gray-200 ml-3 pl-4 space-y-4 py-2">
                    <div v-for="m in milestones" :key="m.id" class="relative">
                      <div class="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-white border-2 border-green-500"></div>
                      <div class="flex justify-between items-start">
                        <div>
                          <p class="font-medium text-gray-900 text-sm">{{ m.title }}</p>
                          <p class="text-xs text-gray-500 mt-0.5">Date Prévue : <span class="font-medium text-gray-700">{{ m.due_date ? new Date(m.due_date).toLocaleDateString('fr-FR') : 'Non définie' }}</span></p>
                        </div>
                        <span class="font-bold text-gray-900 text-sm bg-white px-2 py-1 rounded shadow-sm border border-gray-100">
                          {{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF' }).format(m.amount) }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="mt-4 pt-3 border-t border-gray-200 flex justify-between items-center text-sm font-bold">
                    <span class="text-gray-800">Total à Payer</span>
                    <span class="text-green-600">{{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XOF' }).format(milestones.reduce((sum, m) => sum + m.amount, 0)) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
    <ExcelImportModal 
      :is-open="isImportModalOpen" 
      @close="isImportModalOpen = false" 
      @import="handleImportExcel" 
    />
  </AppLayout>
</template>

<style scoped>
/* Leaflet fixes for broken marker images in Vue 3/Vite */
:deep(.leaflet-default-icon-path) {
  background-image: url('leaflet/dist/images/marker-icon.png');
}
</style>
