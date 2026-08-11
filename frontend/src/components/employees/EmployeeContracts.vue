<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { contractService, type Contract, type ContractCreate } from '@/services/contracts';

const props = defineProps<{
  employeeId: number;
}>();

const contracts = ref<Contract[]>([]);
const loading = ref(true);
const errorMessage = ref('');
const showForm = ref(false);

const sortColumn = ref('');
const sortOrder = ref<'asc' | 'desc'>('asc');

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortOrder.value = 'asc';
  }
};

const sortedContracts = computed(() => {
  if (!sortColumn.value) return contracts.value;
  return [...contracts.value].sort((a, b) => {
    let valA = (a as any)[sortColumn.value];
    let valB = (b as any)[sortColumn.value];

    if (valA === null || valA === undefined) valA = '';
    if (valB === null || valB === undefined) valB = '';

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const form = ref<Omit<ContractCreate, 'employee_id'>>({
  contract_type: 'CDI',
  start_date: '',
  end_date: null,
  is_active: true
});

const loadEmployeeContracts = async () => {
  try {
    loading.value = true;
    const allContracts = await contractService.getAll();
    contracts.value = allContracts.filter(c => c.user_id === props.employeeId);
  } catch (error) {
    errorMessage.value = "Erreur lors du chargement des contrats.";
  } finally {
    loading.value = false;
  }
};

watch(() => props.employeeId, () => {
  loadEmployeeContracts();
}, { immediate: true });

const handleSubmit = async () => {
  try {
    const payload: ContractCreate = {
      ...form.value,
      user_id: props.employeeId,
      end_date: form.value.end_date || null
    };
    await contractService.create(payload);
    showForm.value = false;
    form.value = { contract_type: 'CDI', start_date: '', end_date: null, is_active: true };
    await loadEmployeeContracts();
  } catch (error) {
    errorMessage.value = "Impossible d'enregistrer le contrat.";
  }
};

const handleDelete = async (id: number) => {
  if (confirm('Supprimer ce contrat ?')) {
    try {
      await contractService.delete(id);
      await loadEmployeeContracts();
    } catch (error) {
      console.error(error);
    }
  }
};
</script>

<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <span class="material-symbols-outlined text-[#d10f2f]">history</span>
        <span>Historique des Contrats</span>
      </h3>
      <button 
        @click="showForm = !showForm"
        class="bg-[#d10f2f] hover:bg-[#97091f] text-white text-xs font-medium py-2 px-3 rounded-lg transition-colors inline-flex items-center gap-2"
      >
        <span class="material-symbols-outlined text-sm">post_add</span>
        {{ showForm ? 'Annuler' : 'Nouveau Contrat' }}
      </button>
    </div>

    <div v-if="showForm" class="bg-red-50 p-4 rounded-xl border border-red-100 shadow-inner max-w-md">
      <form @submit.prevent="handleSubmit" class="space-y-3 text-sm">
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Type de contrat</label>
          <select v-model="form.contract_type" class="w-full border border-red-200 rounded-lg p-2 bg-white focus:border-red-300 focus:ring-2 focus:ring-red-100 outline-none">
            <option value="CDI">CDI</option>
            <option value="CDD">CDD</option>
            <option value="Stagiaire">Stagiaire</option>
            <option value="Alternant">Alternant</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Date de début</label>
          <input type="date" v-model="form.start_date" required class="w-full border border-red-200 rounded-lg p-2 bg-white focus:border-red-300 focus:ring-2 focus:ring-red-100 outline-none" />
        </div>
        <div v-if="form.contract_type !== 'CDI'">
          <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Date de fin</label>
          <input type="date" v-model="form.end_date" class="w-full border border-red-200 rounded-lg p-2 bg-white focus:border-red-300 focus:ring-2 focus:ring-red-100 outline-none" />
        </div>
        <div class="flex items-center space-x-2 py-1">
          <input type="checkbox" v-model="form.is_active" id="comp_is_active" class="rounded text-[#d10f2f]" />
          <label for="comp_is_active" class="text-xs text-gray-600">Contrat actif</label>
        </div>
        <button type="submit" class="w-full bg-[#d10f2f] hover:bg-[#97091f] text-white font-medium py-2 rounded-lg transition-colors inline-flex items-center justify-center gap-2">
          <span class="material-symbols-outlined text-sm">save</span>
          Enregistrer le contrat
        </button>
      </form>
    </div>

    <div v-if="loading" class="text-center py-4 text-sm text-gray-400">Chargement des contrats...</div>

    <div v-else class="bg-white border border-red-100 rounded-lg overflow-hidden shadow-xs">
      <table class="min-w-full divide-y divide-red-100 text-left text-xs">
        <thead class="bg-red-50 text-gray-600 font-medium uppercase">
          <tr>
            <th @click="sortBy('contract_type')" class="px-4 py-2 cursor-pointer hover:bg-red-100 transition">
              <div class="flex items-center gap-1">Type <span v-if="sortColumn === 'contract_type'" class="material-symbols-outlined text-[10px]">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
            </th>
            <th @click="sortBy('start_date')" class="px-4 py-2 cursor-pointer hover:bg-red-100 transition">
              <div class="flex items-center gap-1">Début <span v-if="sortColumn === 'start_date'" class="material-symbols-outlined text-[10px]">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
            </th>
            <th @click="sortBy('end_date')" class="px-4 py-2 cursor-pointer hover:bg-red-100 transition">
              <div class="flex items-center gap-1">Fin <span v-if="sortColumn === 'end_date'" class="material-symbols-outlined text-[10px]">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
            </th>
            <th @click="sortBy('is_active')" class="px-4 py-2 cursor-pointer hover:bg-red-100 transition">
              <div class="flex items-center gap-1">Statut <span v-if="sortColumn === 'is_active'" class="material-symbols-outlined text-[10px]">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
            </th>
            <th class="px-4 py-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-red-100 text-gray-600">
          <tr v-for="contract in sortedContracts" :key="contract.id" class="hover:bg-red-50/50">
            <td class="px-4 py-3 font-semibold text-gray-900">{{ contract.contract_type }}</td>
            <td class="px-4 py-3">{{ contract.start_date }}</td>
            <td class="px-4 py-3">{{ contract.end_date || 'Indéterminée' }}</td>
            <td class="px-4 py-3">
              <span :class="contract.is_active ? 'bg-red-100 text-red-700' : 'bg-red-200 text-red-900'" class="px-2 py-0.5 rounded-full text-[10px] font-medium">
                {{ contract.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <button @click="handleDelete(contract.id)" class="text-red-600 hover:text-red-900 font-medium inline-flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">delete</span>
                <span>Supprimer</span>
              </button>
            </td>
          </tr>
          <tr v-if="contracts.length === 0">
            <td colspan="5" class="px-4 py-6 text-center text-gray-400">Aucun contrat enregistré pour cet employé.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>