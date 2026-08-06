<template>
  <div class="space-y-4">
    <div v-if="loading" class="flex justify-center py-4">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#d10f2f]"></div>
    </div>
    
    <div v-else-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg text-sm">
      {{ error }}
    </div>
    
    <div v-else>
      <div class="mb-4 flex items-center justify-between">
        <span class="text-sm font-medium text-gray-700">Disponibilité actuelle:</span>
        <span :class="[availabilityClass, 'px-3 py-1 rounded-full text-xs font-bold']">
          {{ currentAvailability }}%
        </span>
      </div>

      <div v-if="assignments.length === 0" class="text-center text-gray-500 py-4 italic text-sm">
        Aucun projet assigné.
      </div>

      <div v-else class="space-y-3">
        <div v-for="assign in assignments" :key="assign.id" class="p-3 border border-gray-100 rounded-lg bg-gray-50 flex flex-col gap-2">
          <div class="flex justify-between items-start">
            <div>
              <div class="font-bold text-gray-900 text-sm">[{{ assign.project?.code }}] {{ assign.project?.nom }}</div>
              <div class="text-xs text-gray-500">{{ assign.role }}</div>
            </div>
            <span :class="{
              'bg-green-100 text-green-800': assign.current_status === 'Active', 
              'bg-gray-200 text-gray-800': assign.current_status === 'Completed',
              'bg-yellow-100 text-yellow-800': assign.current_status === 'Upcoming'
            }" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase">
              {{ assign.current_status === 'Active' ? 'Actif' : assign.current_status === 'Upcoming' ? 'À venir' : 'Terminé' }}
            </span>
          </div>
          <div class="flex justify-between items-end mt-1">
            <div class="text-xs text-gray-500 flex flex-col gap-0.5">
              <span>Du: {{ formatDate(assign.start_date) }}</span>
              <span v-if="assign.end_date">Au: {{ formatDate(assign.end_date) }}</span>
              <span v-else>Au: (Continu)</span>
            </div>
            <div class="text-sm font-bold text-[#d10f2f]">
              {{ assign.allocation }}%
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { api } from '@/services/api';

const props = defineProps<{
  employeeId: number;
}>();

const assignments = ref<any[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const fetchAssignments = async () => {
  if (!props.employeeId) return;
  loading.value = true;
  error.value = null;
  try {
    const res = await api.get(`/users/${props.employeeId}/assignments`);
    assignments.value = res.data;
  } catch (err) {
    error.value = "Erreur lors du chargement des affectations.";
  } finally {
    loading.value = false;
  }
};

const formatDate = (d: string) => {
  if (!d) return '';
  return new Date(d).toLocaleDateString();
};

const activeAssignments = computed(() => {
  return assignments.value.filter(a => a.current_status === 'Active');
});

const currentAvailability = computed(() => {
  const sum = activeAssignments.value.reduce((acc, curr) => acc + curr.allocation, 0);
  return Math.max(0, 100 - sum);
});

const availabilityClass = computed(() => {
  if (currentAvailability.value === 0) return 'bg-red-100 text-red-700';
  if (currentAvailability.value < 50) return 'bg-yellow-100 text-yellow-700';
  return 'bg-green-100 text-green-700';
});

watch(() => props.employeeId, () => {
  fetchAssignments();
}, { immediate: true });

onMounted(() => {
  if (!loading.value && assignments.value.length === 0) {
    fetchAssignments();
  }
});
</script>
