<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { attendanceService, type TimeclockRecord } from '@/services/attendance'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const record = ref<TimeclockRecord | null>(null)
const loading = ref(false)
const loadingAction = ref<'in' | 'out' | null>(null)

// Timer en direct
const elapsed = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const hasCheckedIn = computed(() => !!record.value?.check_in)
const hasCheckedOut = computed(() => !!record.value?.check_out)

function formatTime(isoStr: string | null | undefined): string {
  if (!isoStr) return '--:--'
  // UTC → local
  const d = new Date(isoStr + 'Z')
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function startTimer() {
  if (timerInterval) clearInterval(timerInterval)
  if (!record.value?.check_in || record.value.check_out) return

  const checkInMs = new Date(record.value.check_in + 'Z').getTime()
  elapsed.value = Math.floor((Date.now() - checkInMs) / 1000)

  timerInterval = setInterval(() => {
    elapsed.value++
  }, 1000)
}

async function loadToday() {
  loading.value = true
  try {
    const res = await attendanceService.getToday()
    record.value = res.data
    startTimer()
  } catch {
    // silently fail
  } finally {
    loading.value = false
  }
}

async function clockIn() {
  loadingAction.value = 'in'
  try {
    const res = await attendanceService.clockIn()
    record.value = res.data
    toast.success('Arrivée enregistrée ! Bonne journée 👋')
    startTimer()
  } catch (e: any) {
    // toast already shown by api interceptor
  } finally {
    loadingAction.value = null
  }
}

async function clockOut() {
  loadingAction.value = 'out'
  try {
    const res = await attendanceService.clockOut()
    record.value = res.data
    if (timerInterval) clearInterval(timerInterval)
    toast.success('Sortie enregistrée ! Bonne fin de journée 🏁')
  } catch (e: any) {
    // toast already shown by api interceptor
  } finally {
    loadingAction.value = null
  }
}

onMounted(loadToday)
onUnmounted(() => { if (timerInterval) clearInterval(timerInterval) })
</script>

<template>
  <div class="attendance-widget">
    <!-- Header -->
    <div class="widget-header">
      <div class="header-icon">
        <span class="material-symbols-outlined">fingerprint</span>
      </div>
      <div>
        <h3 class="widget-title">Mon Pointage</h3>
        <p class="widget-date">{{ new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }) }}</p>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="skeleton-container">
      <div class="skeleton skeleton-row"></div>
      <div class="skeleton skeleton-btn"></div>
    </div>

    <!-- Contenu principal -->
    <div v-else class="widget-body">

      <!-- Status banner -->
      <div v-if="hasCheckedOut" class="status-banner status-done">
        <span class="material-symbols-outlined">check_circle</span>
        <span>Journée terminée</span>
      </div>
      <div v-else-if="hasCheckedIn" class="status-banner status-active">
        <span class="material-symbols-outlined">radio_button_checked</span>
        <span>En service</span>
        <span class="timer-badge">{{ formatElapsed(elapsed) }}</span>
      </div>
      <div v-else class="status-banner status-idle">
        <span class="material-symbols-outlined">schedule</span>
        <span>Pas encore pointé</span>
      </div>

      <!-- Horaires -->
      <div class="time-row">
        <div class="time-block">
          <span class="time-label">
            <span class="material-symbols-outlined text-sm">login</span>
            Arrivée
          </span>
          <span class="time-value" :class="{ 'time-recorded': hasCheckedIn }">
            {{ formatTime(record?.check_in) }}
          </span>
        </div>
        <div class="time-divider">→</div>
        <div class="time-block">
          <span class="time-label">
            <span class="material-symbols-outlined text-sm">logout</span>
            Sortie
          </span>
          <span class="time-value" :class="{ 'time-recorded': hasCheckedOut }">
            {{ formatTime(record?.check_out) }}
          </span>
        </div>
      </div>

      <!-- Durée totale si terminé -->
      <div v-if="hasCheckedOut && record?.check_in && record?.check_out" class="duration-row">
        <span class="material-symbols-outlined">timer</span>
        <span>Durée : {{ formatElapsed(Math.floor((new Date(record.check_out + 'Z').getTime() - new Date(record.check_in + 'Z').getTime()) / 1000)) }}</span>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button
          v-if="!hasCheckedIn"
          @click="clockIn"
          :disabled="loadingAction !== null"
          id="btn-clock-in"
          class="btn btn-checkin"
        >
          <span v-if="loadingAction === 'in'" class="material-symbols-outlined spin">progress_activity</span>
          <span v-else class="material-symbols-outlined">login</span>
          Pointer mon arrivée
        </button>

        <button
          v-else-if="!hasCheckedOut"
          @click="clockOut"
          :disabled="loadingAction !== null"
          id="btn-clock-out"
          class="btn btn-checkout"
        >
          <span v-if="loadingAction === 'out'" class="material-symbols-outlined spin">progress_activity</span>
          <span v-else class="material-symbols-outlined">logout</span>
          Pointer ma sortie
        </button>

        <div v-else class="all-done">
          <span class="material-symbols-outlined">verified</span>
          Pointage du jour complet
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.attendance-widget {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 20px;
  padding: 24px;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  position: relative;
  overflow: hidden;
}

.attendance-widget::before {
  content: '';
  position: absolute;
  top: -40px;
  right: -40px;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: rgba(209, 15, 47, 0.12);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.header-icon {
  background: rgba(209, 15, 47, 0.2);
  border: 1px solid rgba(209, 15, 47, 0.4);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  align-items: center;
}

.header-icon .material-symbols-outlined {
  font-size: 28px;
  color: #ff4d6d;
}

.widget-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: #fff;
}

.widget-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin: 2px 0 0;
  text-transform: capitalize;
}

/* Skeleton */
.skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.skeleton {
  background: linear-gradient(90deg, rgba(255,255,255,0.06) 25%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: 10px;
}
.skeleton-row { height: 40px; }
.skeleton-btn { height: 46px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Status banner */
.status-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
}
.status-banner .material-symbols-outlined { font-size: 18px; }

.status-idle {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
}
.status-active {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.25);
}
.status-done {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.timer-badge {
  margin-left: auto;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  font-weight: 700;
  color: #4ade80;
  letter-spacing: 1px;
}

/* Horaires */
.time-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  padding: 14px 16px;
}

.time-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.time-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.time-label .material-symbols-outlined { font-size: 14px; }

.time-value {
  font-size: 22px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 1px;
}
.time-value.time-recorded { color: #fff; }

.time-divider {
  color: rgba(255, 255, 255, 0.25);
  font-size: 18px;
}

/* Durée */
.duration-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 16px;
  padding-left: 4px;
}
.duration-row .material-symbols-outlined { font-size: 16px; }

/* Buttons */
.actions { margin-top: 4px; }

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 13px 20px;
  border: none;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.3px;
}
.btn:disabled { opacity: 0.7; cursor: not-allowed; }
.btn .material-symbols-outlined { font-size: 20px; }

.btn-checkin {
  background: linear-gradient(135deg, #d10f2f, #ff4d6d);
  color: white;
  box-shadow: 0 4px 20px rgba(209, 15, 47, 0.45);
}
.btn-checkin:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 28px rgba(209, 15, 47, 0.6);
}
.btn-checkin:active:not(:disabled) { transform: translateY(0); }

.btn-checkout {
  background: linear-gradient(135deg, #1d4ed8, #3b82f6);
  color: white;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
}
.btn-checkout:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 28px rgba(59, 130, 246, 0.55);
}
.btn-checkout:active:not(:disabled) { transform: translateY(0); }

.all-done {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 13px;
  background: rgba(255,255,255,0.07);
  border-radius: 14px;
  font-size: 13px;
  color: rgba(255,255,255,0.6);
}
.all-done .material-symbols-outlined { color: #60a5fa; }

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
