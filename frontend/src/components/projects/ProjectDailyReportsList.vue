<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mt-6">
    <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
        </div>
        <div>
          <h2 class="text-lg font-semibold text-gray-800">Rapports Journaliers</h2>
          <p class="text-sm text-gray-500">Suivi de l'avancement de l'équipe</p>
        </div>
      </div>
      
      <div class="flex items-center space-x-3">
        <input type="date" v-model="filterDate" class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" @change="fetchReports" />
      </div>
    </div>

    <div v-if="loading" class="p-8 text-center text-gray-500">
      <div class="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
      Chargement des rapports...
    </div>
    
    <div v-else-if="reports.length === 0" class="p-8 text-center text-gray-500">
      Aucun rapport soumis pour ce projet à cette date.
    </div>

    <div v-else class="divide-y divide-gray-100">
      <div v-for="report in reports" :key="report.id" class="p-6 hover:bg-gray-50 transition-colors">
        <div class="flex justify-between items-start mb-4">
          <div>
            <div class="flex items-center space-x-2">
              <h4 class="font-semibold text-gray-800">Employé #{{ report.employee_id }}</h4>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-yellow-100 text-yellow-800': report.status === 'DRAFT',
                  'bg-blue-100 text-blue-800': report.status === 'SUBMITTED',
                  'bg-green-100 text-green-800': report.status === 'APPROVED'
                }">
                {{ report.status }}
              </span>
            </div>
            <p class="text-sm text-gray-500 mt-1">{{ report.report_date }} • {{ report.hours_worked }} heures travaillées</p>
          </div>
          
          <div class="flex space-x-2" v-if="report.status === 'SUBMITTED'">
            <button @click="updateStatus(report.id, 'APPROVED')" class="px-3 py-1 bg-green-50 text-green-600 hover:bg-green-100 rounded-lg text-sm font-medium transition-colors">
              Approuver
            </button>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div>
            <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Tâches terminées</h5>
            <p class="text-gray-700 whitespace-pre-wrap text-sm">{{ report.tasks_completed }}</p>
          </div>
          
          <div>
            <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Problèmes rencontrés</h5>
            <p class="text-gray-700 whitespace-pre-wrap text-sm italic">{{ report.issues_encountered || 'Aucun' }}</p>
          </div>
          
          <div v-if="report.plan_for_tomorrow" class="md:col-span-2 bg-blue-50/50 p-4 rounded-lg">
            <h5 class="text-xs font-semibold text-blue-800 uppercase tracking-wider mb-1">Plan pour demain</h5>
            <p class="text-blue-900 whitespace-pre-wrap text-sm">{{ report.plan_for_tomorrow }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { dailyReportsService, type DailyReportResponse } from '@/services/daily_reports';
import { useToast } from '@/composables/useToast';

const props = defineProps({
  projectId: {
    type: Number,
    required: false,
    default: null
  }
});

const toast = useToast();
const reports = ref<DailyReportResponse[]>([]);
const loading = ref(false);
const filterDate = ref<string>(''); // Can be used to filter by date

async function fetchReports() {
  if (!props.projectId) return;
  try {
    loading.value = true;
    reports.value = await dailyReportsService.getReports(props.projectId, filterDate.value || undefined);
  } catch (error) {
    console.error("Erreur chargement des rapports", error);
    toast.error("Impossible de charger les rapports journaliers.");
  } finally {
    loading.value = false;
  }
}

async function updateStatus(reportId: number, status: 'DRAFT' | 'SUBMITTED' | 'APPROVED') {
  try {
    await dailyReportsService.updateStatus(reportId, status);
    toast.success(`Rapport ${status === 'APPROVED' ? 'approuvé' : 'mis à jour'}`);
    fetchReports();
  } catch (error) {
    console.error("Erreur update status", error);
    toast.error("Erreur lors de la mise à jour du statut.");
  }
}

onMounted(() => {
  fetchReports();
});

watch(() => props.projectId, () => {
  fetchReports();
});
</script>
