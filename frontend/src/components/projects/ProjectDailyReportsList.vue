<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mt-6">
    <!-- Header -->
    <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-red-100 text-red-600 rounded-xl">
          <span class="material-symbols-outlined text-xl">calendar_month</span>
        </div>
        <div>
          <h2 class="text-lg font-bold text-gray-800">Rapports du Projet</h2>
          <div class="flex gap-4 mt-2">
            <button @click="activeTab = 'weekly'" :class="{'text-red-600 font-bold border-b-2 border-red-600': activeTab === 'weekly', 'text-gray-500 hover:text-gray-700': activeTab !== 'weekly'}" class="pb-1 transition">Hebdomadaires</button>
            <button @click="activeTab = 'daily'" :class="{'text-red-600 font-bold border-b-2 border-red-600': activeTab === 'daily', 'text-gray-500 hover:text-gray-700': activeTab !== 'daily'}" class="pb-1 transition">Journaliers</button>
          </div>
        </div>
      </div>

      <!-- Filtre -->
      <div class="flex items-center gap-2">
        <label class="text-xs font-medium text-gray-500">{{ activeTab === 'weekly' ? 'Semaine :' : 'Date :' }}</label>
        <input
          v-if="activeTab === 'weekly'"
          type="week"
          v-model="filterWeek"
          class="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-red-400 focus:border-red-400 outline-none"
          @change="fetchReports"
        />
        <input
          v-else
          type="date"
          v-model="filterDate"
          class="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-red-400 focus:border-red-400 outline-none"
          @change="fetchReports"
        />
        <button
          v-if="(activeTab === 'weekly' && filterWeek) || (activeTab === 'daily' && filterDate)"
          @click="clearFilters"
          class="text-xs text-gray-400 hover:text-gray-600"
          title="Effacer le filtre"
        >
          <span class="material-symbols-outlined text-base">close</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-10 text-center text-gray-400">
      <span class="material-symbols-outlined text-4xl animate-spin block mb-2">progress_activity</span>
      Chargement des rapports…
    </div>

    <!-- Vide -->
    <div v-else-if="reports.length === 0" class="p-12 text-center">
      <span class="material-symbols-outlined text-5xl text-gray-300 block mb-3">inbox</span>
      <p class="text-gray-500 font-medium">Aucun rapport {{ activeTab === 'weekly' ? 'hebdomadaire' : 'journalier' }}</p>
      <p class="text-gray-400 text-sm mt-1">Aucun rapport n'a été soumis pour cette période.</p>
    </div>

    <!-- Liste des rapports -->
    <div v-else class="divide-y divide-gray-50">
      <div
        v-for="report in reports"
        :key="report.id"
        class="p-6 hover:bg-gray-50/80 transition-colors"
      >
        <!-- En-tête du rapport -->
        <div class="flex justify-between items-start mb-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center text-white text-sm font-bold shadow-sm">
              {{ employeeInitials(report) }}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h4 class="font-semibold text-gray-800">{{ employeeName(report) }}</h4>
                <span
                  class="px-2.5 py-0.5 rounded-full text-xs font-semibold"
                  :class="{
                    'bg-yellow-100 text-yellow-800': report.status === 'DRAFT',
                    'bg-blue-100 text-blue-800': report.status === 'SUBMITTED',
                    'bg-green-100 text-green-800': report.status === 'APPROVED'
                  }"
                >
                  {{ statusLabel(report.status) }}
                </span>
              </div>
              <p class="text-sm text-gray-500 mt-0.5">
                <span class="material-symbols-outlined text-xs align-middle mr-0.5">date_range</span>
                <span v-if="activeTab === 'weekly'">Semaine du {{ fmt(report.week_start) }} au {{ fmt(report.week_end) }}</span>
                <span v-else>Le {{ fmt(report.report_date) }}</span>
                &nbsp;•&nbsp; {{ report.hours_worked }}h travaillées
              </p>
            </div>
          </div>

          <!-- Avancement -->
          <div class="flex items-center gap-4">
            <div v-if="report.progress_percentage != null" class="text-center">
              <div class="relative w-12 h-12">
                <svg class="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="#f3f4f6" stroke-width="3"/>
                  <circle
                    cx="18" cy="18" r="15.9" fill="none"
                    stroke="#d10f2f" stroke-width="3"
                    stroke-dasharray="100"
                    :stroke-dashoffset="100 - report.progress_percentage"
                    stroke-linecap="round"
                  />
                </svg>
                <span class="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-700">
                  {{ report.progress_percentage }}%
                </span>
              </div>
            </div>

            <!-- Approuver -->
            <div v-if="report.status === 'SUBMITTED'">
              <button
                @click="updateStatus(report.id, 'APPROVED')"
                class="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 hover:bg-green-100 rounded-lg text-sm font-medium transition"
              >
                <span class="material-symbols-outlined text-base">check_circle</span>
                Approuver
              </button>
            </div>
          </div>
        </div>

        <!-- Contenu -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="bg-gray-50 rounded-xl p-4">
            <h5 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">task_alt</span>
              Tâches réalisées
            </h5>
            <p class="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">{{ report.tasks_completed }}</p>
          </div>

          <div class="bg-gray-50 rounded-xl p-4">
            <h5 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">warning</span>
              Blocages / Problèmes
            </h5>
            <p class="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed italic">
              {{ report.issues_encountered || 'Aucun blocage signalé' }}
            </p>
          </div>

          <div v-if="report.plan_next_week || report.plan_next_day" class="md:col-span-2 bg-blue-50 rounded-xl p-4 border border-blue-100">
            <h5 class="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-2 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">arrow_forward</span>
              Plan pour la suite
            </h5>
            <p class="text-blue-900 whitespace-pre-wrap text-sm leading-relaxed">{{ report.plan_next_week || report.plan_next_day }}</p>
          </div>

          <!-- Photos -->
          <div v-if="report.photos_urls && report.photos_urls.length > 0" class="md:col-span-2 mt-2">
            <h5 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">image</span>
              Photos jointes
            </h5>
            <div class="flex flex-wrap gap-4 mt-2">
              <a v-for="(url, idx) in report.photos_urls" :key="idx" :href="'http://192.190.100.41:8000' + url" target="_blank" class="block w-24 h-24 rounded-lg overflow-hidden border border-gray-200 hover:opacity-80 transition cursor-pointer">
                <img :src="'http://192.190.100.41:8000' + url" class="w-full h-full object-cover" />
              </a>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { dailyReportsService } from '@/services/daily_reports';
import { useToast } from '@/composables/useToast';

const props = defineProps<{ projectId?: number | null }>();
const toast = useToast();
const reports = ref<any[]>([]);
const loading = ref(false);

const activeTab = ref<'weekly' | 'daily'>('weekly');
const filterWeek = ref('');
const filterDate = ref('');

function employeeName(report: any): string {
  if (report.user) {
    const fullName = `${report.user.first_name || ''} ${report.user.last_name || ''}`.trim();
    if (fullName) return fullName;
    if (report.user.name) return report.user.name;
    if (report.user.email) return report.user.email;
  }
  return `Employé #${report.user_id}`;
}

function employeeInitials(report: any): string {
  if (report.user) {
    const fn = (report.user.first_name || '').trim();
    const ln = (report.user.last_name || '').trim();
    if (fn && ln) {
      return (fn[0] + ln[0]).toUpperCase();
    }
    if (fn) {
      return fn.slice(0, 2).toUpperCase();
    }
    if (report.user.name) {
      const parts = report.user.name.trim().split(' ').filter(Boolean);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return report.user.name.slice(0, 2).toUpperCase();
    }
    if (report.user.email) {
      return report.user.email.slice(0, 2).toUpperCase();
    }
  }
  return String(report.user_id).slice(0, 2);
}

function fmt(dateStr: string): string {
  if (!dateStr) return '';
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

function statusLabel(status: string): string {
  return { DRAFT: 'Brouillon', SUBMITTED: 'Soumis', APPROVED: 'Approuvé' }[status] || status;
}

function weekStartFromIso(isoWeek: string): string | undefined {
  if (!isoWeek) return undefined;
  const [yearStr, weekStr] = isoWeek.split('-W');
  const year = parseInt(yearStr);
  const week = parseInt(weekStr);
  const jan4 = new Date(year, 0, 4);
  const startOfWeek1 = new Date(jan4);
  startOfWeek1.setDate(jan4.getDate() - ((jan4.getDay() + 6) % 7));
  const monday = new Date(startOfWeek1);
  monday.setDate(startOfWeek1.getDate() + (week - 1) * 7);
  return monday.toISOString().split('T')[0];
}

function clearFilters() {
  filterWeek.value = '';
  filterDate.value = '';
  fetchReports();
}

async function fetchReports() {
  if (!props.projectId) return;
  loading.value = true;
  try {
    if (activeTab.value === 'weekly') {
      const weekStart = weekStartFromIso(filterWeek.value);
      reports.value = await dailyReportsService.getReports(props.projectId, weekStart);
    } else {
      reports.value = await dailyReportsService.getDailyReports(props.projectId, filterDate.value || undefined);
    }
  } catch {
    toast.error('Impossible de charger les rapports.');
  } finally {
    loading.value = false;
  }
}

async function updateStatus(reportId: number, status: 'DRAFT' | 'SUBMITTED' | 'APPROVED') {
  try {
    if (activeTab.value === 'weekly') {
      await dailyReportsService.updateStatus(reportId, status);
    } else {
      await dailyReportsService.updateDailyStatus(reportId, status);
    }
    toast.success('Rapport approuvé ✅');
    fetchReports();
  } catch {
    toast.error('Erreur lors de la mise à jour du statut.');
  }
}

onMounted(fetchReports);
watch(() => props.projectId, fetchReports);
watch(activeTab, fetchReports);
</script>
