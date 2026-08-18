<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import api from '@/services/api';
import { useToast } from '@/composables';

const toast = useToast();

interface Department {
  id: number;
  name: string;
  code?: string;
}

interface WeekDay {
  label: string;
  date: string;
  fullDate: string;
}

interface EmployeeSchedule {
  id: number;
  name: string;
  role: string;
  department_id: number;
  department_name?: string;
  schedule: Array<'CHANTIER' | 'SITE' | 'CONGE' | 'NONE'>;
}

const isLoading = ref<boolean>(false);
const isSaving = ref<boolean>(false);
const selectedDepartment = ref<number | ''>('');
const employees = ref<EmployeeSchedule[]>([]);
const departments = ref<Department[]>([]);

const sortColumn = ref('name');
const sortOrder = ref<'asc' | 'desc'>('asc');

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortOrder.value = 'asc';
  }
};

const sortedEmployees = computed(() => {
  if (!sortColumn.value) return employees.value;
  return [...employees.value].sort((a, b) => {
    let valA = (a as any)[sortColumn.value];
    let valB = (b as any)[sortColumn.value];

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const getTodayString = (): string => {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = (today.getMonth() + 1).toString().padStart(2, '0');
  const dd = today.getDate().toString().padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};
const currentDateCursor = ref<string>(getTodayString());
const daysViewWindow = ref<number>(7);

const showModal = ref<boolean>(false);
const selectedEmployee = ref<EmployeeSchedule | null>(null);
const selectedDate = ref<string>('');
const selectedStatus = ref<'CHANTIER' | 'SITE' | 'CONGE'>('SITE');

const currentWeekDays = ref<WeekDay[]>([]);

const calculateGridHeaders = (startDateStr: string, count: number): void => {
  const start = new Date(startDateStr);
  const days: WeekDay[] = [];
  const weekdayFormatter = new Intl.DateTimeFormat('fr-FR', { weekday: 'short' });
  const dayNumberFormatter = new Intl.DateTimeFormat('fr-FR', { day: '2-digit' });
  const normalize = (value: string): string => value.replace('.', '').replace(/\s+/g, ' ').trim();
  const capitalize = (value: string): string => value.charAt(0).toUpperCase() + value.slice(1);

  for (let i = 0; i < count; i++) {
    const nextDate = new Date(start);
    nextDate.setDate(start.getDate() + i);

    const dayFormatter = nextDate.getDate().toString().padStart(2, '0');
    const monthFormatter = (nextDate.getMonth() + 1).toString().padStart(2, '0');
    const yearFormatter = nextDate.getFullYear();

    const dayLabel = capitalize(normalize(weekdayFormatter.format(nextDate)));
    const displayDate = dayNumberFormatter.format(nextDate);

    days.push({
      label: dayLabel,
      date: displayDate,
      fullDate: `${yearFormatter}-${monthFormatter}-${dayFormatter}`
    });
  }
  currentWeekDays.value = days;
};

const fetchDepartments = async (): Promise<void> => {
  try {
    const res = await api.get('/departments');
    departments.value = res.data;
  } catch (error) {
    console.error('Erreur chargement départements', error);
  }
};

const fetchHRData = async (): Promise<void> => {
  isLoading.value = true;
  calculateGridHeaders(currentDateCursor.value, daysViewWindow.value);

  try {
    const params: Record<string, any> = {
      start_date: currentDateCursor.value,
      days_count: daysViewWindow.value
    };
    if (selectedDepartment.value !== '') {
      params.department_id = selectedDepartment.value;
    }
    const res = await api.get(`/hr/schedule-matrix`, { params });
    employees.value = res.data;
  } catch (error) {
    console.error("Erreur d'initialisation du planning RH", error);
    toast.error("Impossible de charger les plannings du personnel.");
  } finally {
    isLoading.value = false;
  }
};

const openAssignmentModal = (emp: EmployeeSchedule, dayIndex: number): void => {
  const targetDay = currentWeekDays.value[dayIndex];
  if (!targetDay || emp.schedule[dayIndex] === 'NONE') return;

  selectedEmployee.value = emp;
  selectedDate.value = targetDay.fullDate;
  selectedStatus.value = (emp.schedule[dayIndex] as 'CHANTIER' | 'SITE' | 'CONGE') || 'SITE';
  showModal.value = true;
};

const submitAssignment = async (): Promise<void> => {
  if (!selectedEmployee.value) return;
  isSaving.value = true;

  try {
    await api.post('/hr/assignment', {
      employee_id: selectedEmployee.value.id,
      date: selectedDate.value,
      status: selectedStatus.value
    });
    toast.success("Affectation mise à jour avec succès");
    showModal.value = false;
    await fetchHRData();
  } catch (error) {
    console.error("Erreur lors de l'affectation", error);
    toast.error("Impossible de sauvegarder les modifications.");
  } finally {
    isSaving.value = false;
  }
};

const shiftTimeline = (daysOffset: number): void => {
  const current = new Date(currentDateCursor.value);
  current.setDate(current.getDate() + daysOffset);

  const yyyy = current.getFullYear();
  const mm = (current.getMonth() + 1).toString().padStart(2, '0');
  const dd = current.getDate().toString().padStart(2, '0');

  currentDateCursor.value = `${yyyy}-${mm}-${dd}`;
};

const setToday = (): void => {
  currentDateCursor.value = getTodayString();
};

watch([currentDateCursor, daysViewWindow, selectedDepartment], () => {
  fetchHRData();
});

const getStatusClasses = (status: 'CHANTIER' | 'SITE' | 'CONGE' | 'NONE'): string => {
  switch (status) {
    case 'CHANTIER':
      return 'bg-red-600 text-white border-red-700 font-semibold shadow-xs cursor-pointer hover:bg-red-700 hover:scale-[1.02]';
    case 'SITE':
      return 'bg-gray-800 text-white border-gray-900 font-semibold shadow-xs cursor-pointer hover:bg-gray-900 hover:scale-[1.02]';
    case 'CONGE':
      return 'bg-amber-400 text-gray-900 border-amber-500 font-bold shadow-xs cursor-pointer hover:bg-amber-500 hover:scale-[1.02]';
    default:
      return 'bg-gray-100 text-gray-400 border-gray-200 font-normal cursor-default';
  }
};

const getStatusText = (status: 'CHANTIER' | 'SITE' | 'CONGE' | 'NONE'): string => {
  switch (status) {
    case 'CHANTIER':
      return 'Chantier';
    case 'SITE':
      return 'Sur Site';
    case 'CONGE':
      return 'Congé';
    default:
      return '-';
  }
};

onMounted(async () => {
  await Promise.all([fetchDepartments(), fetchHRData()]);
});
</script>

<template>
  <AppLayout>
    <div class="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen font-sans">
      <!-- Top Header Row -->
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between border-b border-gray-200 pb-5 mb-6 bg-white p-5 rounded-2xl shadow-xs gap-4">
        <div class="flex items-center space-x-3.5">
          <div class="w-11 h-11 bg-red-50 text-red-600 rounded-xl flex items-center justify-center border border-red-100">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m0 4h3m-3 0H5m3 14v-4m0 0H5m3 0h3m-3A1 1 0 007 9v11a1 1 0 001 1h8a1 1 0 001-1V9a1 1 0 00-1-1H8z" />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Planning & Affectations</h1>
            <p class="text-xs text-gray-500 mt-0.5">Vue globale des déploiements opérationnels et disponibilités par département</p>
          </div>
        </div>

        <!-- Legend -->
        <div class="flex flex-wrap items-center gap-3 text-xs bg-gray-50 p-2.5 rounded-xl border border-gray-200">
          <div class="flex items-center space-x-1.5 px-2 py-1 rounded-md bg-white border border-gray-100 shadow-2xs">
            <span class="w-2.5 h-2.5 bg-red-600 rounded-sm inline-block"></span>
            <span class="font-medium text-gray-700 text-xs">En Chantier</span>
          </div>
          <div class="flex items-center space-x-1.5 px-2 py-1 rounded-md bg-white border border-gray-100 shadow-2xs">
            <span class="w-2.5 h-2.5 bg-gray-800 rounded-sm inline-block"></span>
            <span class="font-medium text-gray-700 text-xs">Sur Site (Bureau)</span>
          </div>
          <div class="flex items-center space-x-1.5 px-2 py-1 rounded-md bg-white border border-gray-100 shadow-2xs">
            <span class="w-2.5 h-2.5 bg-amber-400 rounded-sm inline-block"></span>
            <span class="font-medium text-gray-700 text-xs">Congé Payé</span>
          </div>
          <div class="flex items-center space-x-1.5 px-2 py-1 rounded-md bg-white border border-gray-100 shadow-2xs">
            <span class="w-2.5 h-2.5 bg-gray-300 rounded-sm inline-block"></span>
            <span class="font-medium text-gray-400 text-xs">Repos / Week-end</span>
          </div>
        </div>
      </div>

      <!-- Main Table Card -->
      <div class="bg-white border border-gray-200 rounded-2xl shadow-xs overflow-hidden">
        <!-- Controls Navigation Row Header -->
        <div class="bg-gray-50/80 border-b border-gray-200 px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div class="flex items-center space-x-3 flex-wrap gap-2">
            <!-- Department filter -->
            <select
              v-model="selectedDepartment"
              class="border border-gray-300 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-700 focus:outline-none focus:border-red-500 cursor-pointer shadow-2xs"
            >
              <option value="">Tous les départements</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                {{ dept.name }}
              </option>
            </select>

            <!-- Window View Selector -->
            <select
              v-model.number="daysViewWindow"
              class="border border-gray-300 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-700 focus:outline-none focus:border-red-500 cursor-pointer shadow-2xs"
            >
              <option :value="7">Vue 1 Semaine (7 jours)</option>
              <option :value="14">Vue 2 Semaines (14 jours)</option>
              <option :value="30">Vue 1 Mois (30 jours)</option>
            </select>

            <button
              @click="fetchHRData"
              class="p-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-100 text-gray-600 transition-colors shadow-2xs"
              title="Rafraîchir"
            >
              <span class="material-symbols-outlined text-sm">refresh</span>
            </button>
          </div>

          <div class="flex items-center space-x-2 self-end md:self-auto">
            <button
              @click="shiftTimeline(-daysViewWindow)"
              class="p-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-100 text-gray-600 flex items-center transition-colors shadow-2xs"
              title="Période précédente"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>

            <input
              type="date"
              v-model="currentDateCursor"
              class="border border-gray-300 rounded-lg px-3 py-1.5 text-xs text-gray-800 bg-white focus:outline-none font-medium cursor-pointer shadow-2xs"
            />

            <button
              @click="setToday"
              class="px-3.5 py-1.5 border border-gray-300 rounded-lg bg-white text-xs text-gray-700 font-semibold hover:bg-gray-100 transition-colors shadow-2xs"
            >
              Aujourd'hui
            </button>

            <button
              @click="shiftTimeline(daysViewWindow)"
              class="p-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-100 text-gray-600 flex items-center transition-colors shadow-2xs"
              title="Période suivante"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="py-16 text-center text-gray-500">
          <div class="inline-block animate-spin w-8 h-8 border-3 border-red-600 border-t-transparent rounded-full mb-3"></div>
          <p class="text-sm font-medium">Chargement du planning...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="sortedEmployees.length === 0" class="py-16 text-center text-gray-400">
          <span class="material-symbols-outlined text-4xl mb-2 text-gray-300">group_off</span>
          <p class="text-sm font-medium">Aucun collaborateur trouvé pour les critères sélectionnés.</p>
        </div>

        <!-- Matrix Calendar Table Grid -->
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse table-fixed min-w-[800px]">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase text-xxs tracking-wider font-bold h-12">
                <th
                  @click="sortBy('name')"
                  class="px-6 py-2 font-bold text-gray-700 w-64 sticky left-0 bg-gray-50 z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)] cursor-pointer hover:bg-gray-100 transition"
                >
                  <div class="flex items-center gap-2">
                    Collaborateurs
                    <span v-if="sortColumn === 'name'" class="material-symbols-outlined text-xs">
                      {{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}
                    </span>
                  </div>
                </th>
                <th
                  v-for="day in currentWeekDays"
                  :key="day.fullDate"
                  class="px-2 py-2 text-center border-l border-gray-200/40"
                  :class="day.fullDate === getTodayString() ? 'bg-red-50/50' : ''"
                >
                  <div class="text-gray-900 text-xs font-bold leading-none">{{ day.label }}</div>
                  <div class="text-xxs font-medium mt-1 text-gray-400">{{ day.date }}</div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 text-sm text-gray-700">
              <tr v-for="emp in sortedEmployees" :key="emp.id" class="hover:bg-gray-50/50 transition-colors">
                <td class="px-6 py-3.5 whitespace-nowrap border-r border-gray-200 sticky left-0 bg-white z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]">
                  <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-red-100 text-red-700 font-bold text-xs rounded-full flex items-center justify-center uppercase shrink-0">
                      {{ emp.name.substring(0, 2) }}
                    </div>
                    <div class="truncate">
                      <span class="block text-sm font-semibold text-gray-800 truncate">{{ emp.name }}</span>
                      <span class="block text-xxs text-gray-400 font-medium mt-0.5 truncate">
                        {{ emp.role }} <span v-if="emp.department_name" class="text-gray-300">· {{ emp.department_name }}</span>
                      </span>
                    </div>
                  </div>
                </td>

                <td
                  v-for="(status, index) in emp.schedule"
                  :key="index"
                  class="p-1 border-l border-gray-100 text-center align-middle whitespace-nowrap"
                  :class="currentWeekDays[index]?.fullDate === getTodayString() ? 'bg-red-50/30' : ''"
                >
                  <div
                    @click="openAssignmentModal(emp, index)"
                    :class="getStatusClasses(status)"
                    class="mx-auto rounded-lg py-1.5 px-1 text-[10px] border uppercase tracking-wider font-bold min-h-[30px] flex items-center justify-center max-w-[85px] transition-all"
                  >
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- INTERACTIVE ASSIGNMENT MODAL OVERLAY -->
      <div v-if="showModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-sm w-full shadow-2xl border border-gray-100 overflow-hidden">
          <div class="bg-gray-900 px-5 py-4 text-white flex justify-between items-center">
            <div>
              <h3 class="font-bold text-base">Modifier l'affectation</h3>
              <p class="text-xxs text-gray-400 mt-0.5">Date : {{ selectedDate }}</p>
            </div>
            <button @click="showModal = false" class="text-white/80 hover:text-white focus:outline-none">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <div class="p-5 space-y-4">
            <div>
              <p class="text-xs text-gray-400 font-semibold mb-1 uppercase tracking-wide">Collaborateur</p>
              <p class="text-sm font-bold text-gray-800">{{ selectedEmployee?.name }}</p>
              <p class="text-xs text-gray-500">{{ selectedEmployee?.role }}</p>
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wide mb-2">Choisir le statut</label>
              <div class="grid grid-cols-1 gap-2">
                <label
                  class="flex items-center space-x-3 p-3 border rounded-xl cursor-pointer transition-colors"
                  :class="selectedStatus === 'SITE' ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900' : 'border-gray-200 hover:bg-gray-50'"
                >
                  <input type="radio" value="SITE" v-model="selectedStatus" class="text-gray-900 focus:ring-gray-900" />
                  <span class="text-xs font-bold text-gray-800">Sur Site (Bureau)</span>
                </label>

                <label
                  class="flex items-center space-x-3 p-3 border rounded-xl cursor-pointer transition-colors"
                  :class="selectedStatus === 'CHANTIER' ? 'border-red-600 bg-red-50/40 ring-1 ring-red-600' : 'border-gray-200 hover:bg-gray-50'"
                >
                  <input type="radio" value="CHANTIER" v-model="selectedStatus" class="text-red-600 focus:ring-red-600" />
                  <span class="text-xs font-bold text-gray-800">En Chantier</span>
                </label>

                <label
                  class="flex items-center space-x-3 p-3 border rounded-xl cursor-pointer transition-colors"
                  :class="selectedStatus === 'CONGE' ? 'border-amber-500 bg-amber-50/40 ring-1 ring-amber-500' : 'border-gray-200 hover:bg-gray-50'"
                >
                  <input type="radio" value="CONGE" v-model="selectedStatus" class="text-amber-500 focus:ring-amber-500" />
                  <span class="text-xs font-bold text-gray-800">Congé Payé</span>
                </label>
              </div>
            </div>

            <div class="flex justify-end space-x-3 pt-2">
              <button
                type="button"
                @click="showModal = false"
                class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-xs font-semibold hover:bg-gray-50 transition"
              >
                Annuler
              </button>
              <button
                type="button"
                @click="submitAssignment"
                :disabled="isSaving"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg text-xs shadow-xs disabled:opacity-50 transition"
              >
                {{ isSaving ? 'Enregistrement...' : 'Confirmer' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>