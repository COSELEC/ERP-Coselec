<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import AppLayout from '@/layouts/AppLayout.vue'
import { attendanceService, type TimeclockHistoryItem } from '@/services/attendance'

const todayRecords = ref<TimeclockHistoryItem[]>([])
const historyRecords = ref<TimeclockHistoryItem[]>([])
const loading = ref(false)
const activeTab = ref<'today' | 'history'>('today')
const searchQuery = ref('')

function formatDateTime(isoStr: string | null | undefined): string {
  if (!isoStr) return '--:--'
  return new Date(isoStr + 'Z').toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(isoStr: string | null | undefined): string {
  if (!isoStr) return '---'
  return new Date(isoStr + 'Z').toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatDuration(minutes: number | null): string {
  if (minutes === null) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h${String(m).padStart(2, '0')}`
}

function getStatusClass(record: TimeclockHistoryItem): string {
  if (record.check_out) return 'badge-done'
  if (record.check_in) return 'badge-active'
  return 'badge-absent'
}

function getStatusLabel(record: TimeclockHistoryItem): string {
  if (record.check_out) return 'Terminé'
  if (record.check_in) return 'En service'
  return 'Absent'
}

const filteredToday = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return todayRecords.value.filter(r => r.user_name.toLowerCase().includes(q))
})

const filteredHistory = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return historyRecords.value.filter(r => r.user_name.toLowerCase().includes(q))
})

const presentCount = computed(() => todayRecords.value.filter(r => r.check_in).length)
const finishedCount = computed(() => todayRecords.value.filter(r => r.check_out).length)
const activeCount = computed(() => todayRecords.value.filter(r => r.check_in && !r.check_out).length)

async function loadData() {
  loading.value = true
  try {
    const [todayRes, histRes] = await Promise.all([
      attendanceService.getTodayAll(),
      attendanceService.getHistory(30)
    ])
    todayRecords.value = todayRes.data
    historyRecords.value = histRes.data
  } catch {
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-6 w-full">

      <!-- Header -->
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Suivi des Pointages</h1>
          <p class="mt-1 text-gray-500">Vue d'ensemble des arrivées et sorties des employés</p>
        </div>
        <button @click="loadData" :disabled="loading" class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition shadow-sm">
          <span class="material-symbols-outlined text-base" :class="{ 'spin': loading }">refresh</span>
          Actualiser
        </button>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="stat-card stat-present">
          <span class="material-symbols-outlined stat-icon">people</span>
          <div>
            <p class="stat-label">Présents aujourd'hui</p>
            <p class="stat-value">{{ presentCount }}</p>
          </div>
        </div>
        <div class="stat-card stat-active">
          <span class="material-symbols-outlined stat-icon">radio_button_checked</span>
          <div>
            <p class="stat-label">En service</p>
            <p class="stat-value">{{ activeCount }}</p>
          </div>
        </div>
        <div class="stat-card stat-done">
          <span class="material-symbols-outlined stat-icon">check_circle</span>
          <div>
            <p class="stat-label">Journées terminées</p>
            <p class="stat-value">{{ finishedCount }}</p>
          </div>
        </div>
      </div>

      <!-- Tabs + Search -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="flex items-center justify-between p-4 border-b border-gray-100">
          <div class="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              @click="activeTab = 'today'"
              :class="['tab-btn', activeTab === 'today' ? 'tab-active' : '']"
            >
              <span class="material-symbols-outlined text-sm">today</span>
              Aujourd'hui
            </button>
            <button
              @click="activeTab = 'history'"
              :class="['tab-btn', activeTab === 'history' ? 'tab-active' : '']"
            >
              <span class="material-symbols-outlined text-sm">history</span>
              Historique (30j)
            </button>
          </div>

          <div class="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2">
            <span class="material-symbols-outlined text-gray-400 text-base">search</span>
            <input
              v-model="searchQuery"
              placeholder="Rechercher un employé..."
              class="bg-transparent text-sm text-gray-700 outline-none w-48"
            />
          </div>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table v-if="!loading" class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                <th class="px-6 py-3 text-left font-medium">Employé</th>
                <th v-if="activeTab === 'history'" class="px-6 py-3 text-left font-medium">Date</th>
                <th class="px-6 py-3 text-left font-medium">Arrivée</th>
                <th class="px-6 py-3 text-left font-medium">Sortie</th>
                <th class="px-6 py-3 text-left font-medium">Durée</th>
                <th class="px-6 py-3 text-left font-medium">Statut</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="r in activeTab === 'today' ? filteredToday : filteredHistory"
                :key="r.id"
                class="hover:bg-gray-50 transition"
              >
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="avatar-circle">{{ r.user_name.charAt(0).toUpperCase() }}</div>
                    <span class="font-medium text-gray-800">{{ r.user_name }}</span>
                  </div>
                </td>
                <td v-if="activeTab === 'history'" class="px-6 py-4 text-gray-600">
                  {{ formatDate(r.date) }}
                </td>
                <td class="px-6 py-4">
                  <span class="flex items-center gap-1.5 text-emerald-600 font-mono font-semibold">
                    <span class="material-symbols-outlined text-sm">login</span>
                    {{ formatDateTime(r.check_in) }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <span class="flex items-center gap-1.5 font-mono font-semibold" :class="r.check_out ? 'text-blue-600' : 'text-gray-400'">
                    <span class="material-symbols-outlined text-sm">logout</span>
                    {{ formatDateTime(r.check_out) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-gray-700 font-medium">
                  {{ formatDuration(r.duration_minutes) }}
                </td>
                <td class="px-6 py-4">
                  <span :class="['badge', getStatusClass(r)]">{{ getStatusLabel(r) }}</span>
                </td>
              </tr>
              <tr v-if="(activeTab === 'today' ? filteredToday : filteredHistory).length === 0">
                <td colspan="6" class="px-6 py-16 text-center text-gray-400">
                  <span class="material-symbols-outlined text-4xl block mb-2">inbox</span>
                  Aucun pointage trouvé
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Skeleton loading -->
          <div v-else class="p-6 space-y-3">
            <div v-for="i in 5" :key="i" class="h-12 bg-gray-100 rounded-xl animate-pulse"></div>
          </div>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<style scoped>
/* Stat cards */
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
  border: 1px solid transparent;
}
.stat-icon { font-size: 32px; }
.stat-label { font-size: 13px; color: inherit; opacity: 0.75; margin: 0; }
.stat-value { font-size: 28px; font-weight: 800; margin: 0; }

.stat-present {
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border-color: #bbf7d0;
  color: #166534;
}
.stat-active {
  background: linear-gradient(135deg, #fefce8, #fef9c3);
  border-color: #fde68a;
  color: #92400e;
}
.stat-done {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  border-color: #bfdbfe;
  color: #1e40af;
}

/* Tabs */
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
}
.tab-active {
  background: white;
  color: #111827;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  font-weight: 600;
}

/* Avatar */
.avatar-circle {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #d10f2f, #ff4d6d);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

/* Badges */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.badge-done { background: #dbeafe; color: #1d4ed8; }
.badge-active { background: #dcfce7; color: #15803d; }
.badge-absent { background: #f3f4f6; color: #6b7280; }

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
