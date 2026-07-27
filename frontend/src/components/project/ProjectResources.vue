<template>
  <div class="flex flex-col gap-6">
    
    <!-- Ressources Humaines Section -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center">
        <h2 class="text-xl font-bold text-gray-900">Ressources Humaines</h2>
        <button @click="openHRAssignmentModal()" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium">
          <span class="material-symbols-outlined text-sm">person_add</span>
          Affecter un employé
        </button>
      </div>
      
      <div class="p-6" v-if="loadingHR">
        <div class="flex justify-center items-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
        </div>
      </div>
      
      <div class="p-6" v-else-if="errorHR">
        <div class="bg-red-50 text-red-600 p-4 rounded-lg text-sm">{{ errorHR }}</div>
      </div>

      <div class="overflow-x-auto" v-else>
        <table class="w-full text-left">
          <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
            <tr>
              <th class="px-6 py-4 font-medium">Employé</th>
              <th class="px-6 py-4 font-medium">Rôle</th>
              <th class="px-6 py-4 font-medium">Allocation</th>
              <th class="px-6 py-4 font-medium">Période</th>
              <th class="px-6 py-4 font-medium">Statut</th>
              <th class="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="assign in hrAssignments" :key="assign.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-red-100 text-[#d10f2f] flex items-center justify-center font-bold text-sm">
                    {{ assign.employee?.first_name?.[0] || '?' }}
                  </div>
                  <div>
                    <div class="font-bold text-gray-900">{{ assign.employee?.first_name }} {{ assign.employee?.last_name }}</div>
                    <div class="text-xs text-gray-500">{{ assign.employee?.position || 'N/A' }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ assign.role }}</td>
              <td class="px-6 py-4 text-sm font-bold text-[#d10f2f]">{{ assign.allocation }}%</td>
              <td class="px-6 py-4 text-sm text-gray-500">
                {{ formatDate(assign.start_date) }}
                <span v-if="assign.end_date"> au {{ formatDate(assign.end_date) }}</span>
                <span v-else> (Continu)</span>
              </td>
              <td class="px-6 py-4">
                <span :class="{
                  'bg-green-100 text-green-800': assign.current_status === 'Active', 
                  'bg-gray-100 text-gray-800': assign.current_status === 'Completed',
                  'bg-yellow-100 text-yellow-800': assign.current_status === 'Upcoming'
                }" class="px-2 py-1 text-xs font-semibold rounded-full">
                  {{ assign.current_status === 'Active' ? 'Actif' : assign.current_status === 'Upcoming' ? 'À venir' : 'Terminé' }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button @click="openHRAssignmentModal(assign)" class="text-gray-400 hover:text-[#d10f2f]" title="Modifier">
                    <span class="material-symbols-outlined text-lg">edit</span>
                  </button>
                  <button @click="removeHRAssignment(assign.id)" class="text-gray-400 hover:text-red-600" title="Retirer">
                    <span class="material-symbols-outlined text-lg">delete</span>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="hrAssignments.length === 0">
              <td colspan="6" class="px-6 py-8 text-center text-gray-500">Aucune ressource humaine affectée à ce projet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Ressources Matérielles Section -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center">
        <h2 class="text-xl font-bold text-gray-900">Ressources Matérielles (Réservations de Stock)</h2>
        <router-link to="/stock-reservations" class="text-sm text-[#d10f2f] hover:underline font-medium flex items-center gap-1">
          <span class="material-symbols-outlined text-sm">open_in_new</span>
          Gérer les réservations
        </router-link>
      </div>
      
      <div class="p-6" v-if="loadingMat">
        <div class="flex justify-center items-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
        </div>
      </div>
      
      <div class="p-6" v-else-if="errorMat">
        <div class="bg-red-50 text-red-600 p-4 rounded-lg text-sm">{{ errorMat }}</div>
      </div>

      <div class="overflow-x-auto" v-else>
        <table class="w-full text-left">
          <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
            <tr>
              <th class="px-6 py-4 font-medium">ID Réservation</th>
              <th class="px-6 py-4 font-medium">Produit</th>
              <th class="px-6 py-4 font-medium">Quantité</th>
              <th class="px-6 py-4 font-medium">Date de Réservation</th>
              <th class="px-6 py-4 font-medium">Statut</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="res in reservations" :key="res.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 text-sm font-bold text-gray-900">RES-{{ res.id }}</td>
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ res.product_name || `Produit #${res.product_id}` }}</td>
              <td class="px-6 py-4 text-sm font-bold text-gray-900">{{ res.quantity }}</td>
              <td class="px-6 py-4 text-sm text-gray-500">{{ formatDate(res.created_at) }}</td>
              <td class="px-6 py-4">
                <span :class="{'bg-green-100 text-green-800': res.status === 'Approved' || res.status === 'Consumed', 'bg-yellow-100 text-yellow-800': res.status === 'Pending'}" class="px-2 py-1 text-xs font-semibold rounded-full">
                  {{ res.status }}
                </span>
              </td>
            </tr>
            <tr v-if="reservations.length === 0">
              <td colspan="5" class="px-6 py-8 text-center text-gray-500">Aucune ressource matérielle réservée pour ce projet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- HR Assignment Modal -->
    <div v-if="showHRModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-full max-w-lg shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">{{ hrForm.id ? 'Modifier l\'affectation' : 'Affecter un employé' }}</h2>
        <form @submit.prevent="saveHRAssignment" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Employé *</label>
            <select v-model="hrForm.employee_id" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" :disabled="!!hrForm.id">
              <option value="" disabled>Sélectionner un employé</option>
              <option v-for="emp in allEmployees" :key="emp.id" :value="emp.id">
                {{ emp.first_name }} {{ emp.last_name }} ({{ emp.position }})
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Rôle *</label>
            <input v-model="hrForm.role" placeholder="ex: Chef de chantier" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Allocation (%) *</label>
            <input type="number" v-model.number="hrForm.allocation" min="1" max="100" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            <p class="text-xs text-gray-500 mt-1">Le total des allocations actives d'un employé ne peut dépasser 100%.</p>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Date de début *</label>
              <input type="date" v-model="hrForm.start_date" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Date de fin (Optionnel)</label>
              <input type="date" v-model="hrForm.end_date" class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="hrForm.notes" rows="2" class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500"></textarea>
          </div>
          
          <div class="flex justify-end gap-2 mt-6">
            <button type="button" @click="showHRModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">Annuler</button>
            <button type="submit" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center min-w-[100px]">
              <span v-if="savingHR" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              <span v-else>Enregistrer</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import api from '@/services/api';
import { useToast } from '@/composables/useToast';

const props = defineProps<{
  projectId: number | string | null
}>();

const toast = useToast();

// Material Resources State
const reservations = ref<any[]>([]);
const loadingMat = ref(false);
const errorMat = ref<string | null>(null);

// Human Resources State
const hrAssignments = ref<any[]>([]);
const allEmployees = ref<any[]>([]);
const loadingHR = ref(false);
const errorHR = ref<string | null>(null);
const showHRModal = ref(false);
const savingHR = ref(false);

const hrForm = ref({
  id: null as number | null,
  employee_id: '' as string | number,
  role: '',
  allocation: 100,
  start_date: '',
  end_date: '',
  notes: ''
});

const formatDate = (dateStr: string) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString();
};

const fetchMaterialResources = async () => {
  if (!props.projectId) {
    reservations.value = [];
    return;
  }
  loadingMat.value = true;
  errorMat.value = null;
  try {
    const res = await api.get('/stock-reservations/');
    reservations.value = res.data.filter((r: any) => String(r.project_id) === String(props.projectId));
  } catch (err: any) {
    errorMat.value = "Impossible de charger les ressources matérielles.";
    console.error(err);
  } finally {
    loadingMat.value = false;
  }
};

const fetchHRResources = async () => {
  if (!props.projectId) {
    hrAssignments.value = [];
    return;
  }
  loadingHR.value = true;
  errorHR.value = null;
  try {
    const res = await api.get(`/projects/${props.projectId}/assignments`);
    hrAssignments.value = res.data;
  } catch (err: any) {
    errorHR.value = "Impossible de charger les ressources humaines.";
    console.error(err);
  } finally {
    loadingHR.value = false;
  }
};

const fetchAllEmployees = async () => {
  try {
    const res = await api.get('/employees/');
    allEmployees.value = res.data;
  } catch (err) {
    console.error("Erreur lors du chargement des employés", err);
  }
};

const openHRAssignmentModal = (assign: any = null) => {
  if (assign) {
    hrForm.value = {
      id: assign.id,
      employee_id: assign.employee_id,
      role: assign.role,
      allocation: assign.allocation,
      start_date: assign.start_date,
      end_date: assign.end_date || '',
      notes: assign.notes || ''
    };
  } else {
    hrForm.value = {
      id: null,
      employee_id: '',
      role: '',
      allocation: 100,
      start_date: new Date().toISOString().split('T')[0] as string,
      end_date: '',
      notes: ''
    };
  }
  showHRModal.value = true;
};

const saveHRAssignment = async () => {
  if (!props.projectId) return;
  savingHR.value = true;
  
  const payload: any = { ...hrForm.value };
  if (!payload.end_date) delete payload.end_date;
  if (!payload.notes) delete payload.notes;

  try {
    if (payload.id) {
      await api.patch(`/projects/assignments/${payload.id}`, payload);
      toast.success("Affectation modifiée avec succès.");
    } else {
      await api.post(`/projects/${props.projectId}/assignments`, payload);
      toast.success("Employé affecté avec succès.");
    }
    showHRModal.value = false;
    fetchHRResources();
  } catch (err: any) {
    const errorDetail = err.response?.data?.detail;
    toast.error(errorDetail || "Erreur lors de l'enregistrement de l'affectation.");
  } finally {
    savingHR.value = false;
  }
};

const removeHRAssignment = async (id: number) => {
  if (!confirm("Voulez-vous vraiment retirer cet employé du projet ?")) return;
  try {
    await api.delete(`/projects/assignments/${id}`);
    toast.success("Employé retiré du projet.");
    fetchHRResources();
  } catch (err: any) {
    toast.error("Erreur lors de la suppression de l'affectation.");
  }
};

watch(() => props.projectId, () => {
  fetchMaterialResources();
  fetchHRResources();
}, { immediate: true });

onMounted(() => {
  fetchAllEmployees();
  if (!loadingMat.value && reservations.value.length === 0) fetchMaterialResources();
  if (!loadingHR.value && hrAssignments.value.length === 0) fetchHRResources();
});
</script>
