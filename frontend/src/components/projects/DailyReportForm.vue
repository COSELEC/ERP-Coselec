<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" v-if="isOpen">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">

      <!-- Header -->
      <div class="flex justify-between items-center px-7 py-5 bg-gradient-to-r from-[#b30c27] to-[#d10f2f] text-white">
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-2xl">calendar_month</span>
          <div>
            <h3 class="text-lg font-bold">Rapport Hebdomadaire</h3>
            <p class="text-xs text-red-100 mt-0.5">{{ weekLabel }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="p-1.5 hover:bg-white/20 rounded-lg transition">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="p-7 overflow-y-auto max-h-[75vh]">
        <form @submit.prevent="handleSubmit" class="space-y-5">

          <!-- Semaine + Projet -->
          <div class="grid grid-cols-2 gap-5">
            <div>
              <label class="field-label">Projet <span class="text-red-500">*</span></label>
              <select v-model="form.project_id" required class="field-input">
                <option value="">Sélectionner un projet</option>
                <option v-for="p in myProjects" :key="p.id" :value="p.id">{{ p.nom }}</option>
              </select>
            </div>

            <div>
              <label class="field-label">Semaine <span class="text-red-500">*</span></label>
              <input
                type="week"
                v-model="selectedWeek"
                required
                class="field-input"
                @change="updateWeekDates"
              />
              <p v-if="weekLabel" class="text-xs text-gray-500 mt-1">{{ weekLabel }}</p>
            </div>
          </div>

          <!-- Heures + Avancement -->
          <div class="grid grid-cols-2 gap-5">
            <div>
              <label class="field-label">Heures travaillées (semaine) <span class="text-red-500">*</span></label>
              <input
                type="number"
                step="0.5"
                min="0"
                v-model="form.hours_worked"
                required
                placeholder="ex: 40"
                class="field-input"
              />
            </div>
            <div>
              <label class="field-label">Avancement global (%)</label>
              <div class="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  v-model="form.progress_percentage"
                  placeholder="ex: 65"
                  class="field-input pr-8"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
              </div>
              <!-- Barre de progression visuelle -->
              <div v-if="form.progress_percentage" class="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-red-500 to-orange-400 rounded-full transition-all"
                  :style="`width: ${form.progress_percentage}%`"
                ></div>
              </div>
            </div>
          </div>

          <!-- Tâches réalisées -->
          <div>
            <label class="field-label">Tâches réalisées cette semaine <span class="text-red-500">*</span></label>
            <textarea
              v-model="form.tasks_completed"
              required
              rows="4"
              placeholder="- Tâche 1 terminée&#10;- Réunion de coordination&#10;- Livraison partielle…"
              class="field-input resize-none"
            ></textarea>
          </div>

          <!-- Problèmes + Plan -->
          <div class="grid grid-cols-1 gap-5">
            <div>
              <label class="field-label">Blocages / Problèmes rencontrés</label>
              <textarea
                v-model="form.issues_encountered"
                rows="2"
                placeholder="Décrivez les difficultés, risques ou points de blocage…"
                class="field-input resize-none"
              ></textarea>
            </div>

            <div>
              <label class="field-label">Plan pour la semaine prochaine</label>
              <textarea
                v-model="form.plan_next_week"
                rows="2"
                placeholder="Ce qui est prévu pour la prochaine semaine…"
                class="field-input resize-none"
              ></textarea>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex justify-end gap-3 pt-3 border-t border-gray-100">
            <button
              type="button"
              @click="$emit('close')"
              class="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition"
            >
              Annuler
            </button>
            <button
              type="submit"
              :disabled="loading"
              class="px-6 py-2.5 bg-gradient-to-r from-[#b30c27] to-[#d10f2f] text-white rounded-xl font-semibold flex items-center gap-2 shadow-md shadow-red-500/25 hover:opacity-90 transition disabled:opacity-60"
            >
              <span v-if="loading" class="material-symbols-outlined spin text-lg">progress_activity</span>
              <span v-else class="material-symbols-outlined text-lg">send</span>
              Soumettre le rapport
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useToast } from '@/composables/useToast';
import { dailyReportsService, type WeeklyReportCreate } from '@/services/daily_reports';
import { api } from '@/services/api';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits(['close', 'report-submitted']);

const toast = useToast();
const loading = ref(false);
const myProjects = ref<any[]>([]);
const selectedWeek = ref('');

function isoWeekToMondayFriday(isoWeek: string): { monday: string; friday: string } | null {
  if (!isoWeek) return null;
  const [yearStr, weekStr] = isoWeek.split('-W');
  const year = parseInt(yearStr);
  const week = parseInt(weekStr);

  const jan4 = new Date(year, 0, 4);
  const startOfWeek1 = new Date(jan4);
  startOfWeek1.setDate(jan4.getDate() - ((jan4.getDay() + 6) % 7));

  const monday = new Date(startOfWeek1);
  monday.setDate(startOfWeek1.getDate() + (week - 1) * 7);
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);

  return {
    monday: monday.toISOString().split('T')[0],
    friday: friday.toISOString().split('T')[0],
  };
}

const form = ref<WeeklyReportCreate>({
  project_id: '' as any,
  report_date: new Date().toISOString().split('T')[0],
  week_start: '',
  week_end: '',
  hours_worked: '' as any,
  progress_percentage: '' as any,
  tasks_completed: '',
  issues_encountered: '',
  plan_next_week: '',
});

function initCurrentWeek() {
  const today = new Date();
  const year = today.getFullYear();
  const startOfYear = new Date(year, 0, 1);
  const dayOfYear = Math.floor((today.getTime() - startOfYear.getTime()) / 86400000);
  const weekNum = Math.ceil((dayOfYear + startOfYear.getDay() + 1) / 7);
  selectedWeek.value = `${year}-W${String(weekNum).padStart(2, '0')}`;
  updateWeekDates();
}

function updateWeekDates() {
  const bounds = isoWeekToMondayFriday(selectedWeek.value);
  if (bounds) {
    form.value.week_start = bounds.monday;
    form.value.week_end = bounds.friday;
    form.value.report_date = new Date().toISOString().split('T')[0];
  }
}

const weekLabel = computed(() => {
  if (!form.value.week_start || !form.value.week_end) return '';
  const fmt = (d: string) => new Date(d + 'T00:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  return `Semaine du ${fmt(form.value.week_start)} au ${fmt(form.value.week_end)}`;
});

onMounted(async () => {
  initCurrentWeek();
  try {
    const res = await api.get('/projects');
    myProjects.value = res.data.filter((p: any) => !['Terminé', 'Clôturé', 'Annulé'].includes(p.status));
  } catch (e) {
    console.error('Error fetching projects', e);
  }
});

async function handleSubmit() {
  try {
    loading.value = true;
    const payload = { ...form.value };
    if (!payload.progress_percentage) delete payload.progress_percentage;

    await dailyReportsService.submitReport(payload as any);
    toast.success('Rapport hebdomadaire soumis avec succès ! ✅');

    form.value = {
      project_id: '' as any,
      report_date: new Date().toISOString().split('T')[0],
      week_start: '',
      week_end: '',
      hours_worked: '' as any,
      progress_percentage: '' as any,
      tasks_completed: '',
      issues_encountered: '',
      plan_next_week: '',
    };
    initCurrentWeek();

    emit('report-submitted');
    emit('close');
  } catch (error: any) {
    console.error('Erreur soumission rapport hebdomadaire', error);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
}
.field-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  color: #111827;
  background: #f9fafb;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.field-input:focus {
  border-color: #d10f2f;
  box-shadow: 0 0 0 3px rgba(209, 15, 47, 0.1);
  background: white;
}
.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
