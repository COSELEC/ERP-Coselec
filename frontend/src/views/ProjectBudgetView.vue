<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import AppLayout from "@/layouts/AppLayout.vue";
import api from "@/services/api";
import { useToast } from '@/composables/useToast';
import { getStoredProfile, hasAnyRole } from '@/services/session';

const toast = useToast();

const currentUser = getStoredProfile();
const canManageBudget = ref(true);

const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const budgets = ref<any[]>([]);
const expenses = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const showBudgetModal = ref(false);
const showExpenseModal = ref(false);
const budgetForm = ref({ id: null as number | null, category: '', allocated_amount: 0, currency: 'XOF' });
const expenseForm = ref({ budget_id: null as number | null, amount: 0, date_incurred: '', description: '' });

const fetchProjects = async () => {
  try {
    const res = await api.get('/projects/');
    projects.value = res.data;
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id;
    } else {
      loading.value = false;
    }
  } catch {
    error.value = "Erreur lors du chargement des projets.";
    loading.value = false;
  }
};

const fetchBudgetData = async () => {
  if (!selectedProjectId.value) return;
  loading.value = true;
  error.value = null;
  try {
    const [budgetsRes, expensesRes] = await Promise.all([
      api.get(`/projects/${selectedProjectId.value}/budgets`),
      api.get(`/projects/${selectedProjectId.value}/budgets/expenses`)
    ]);
    budgets.value = budgetsRes.data;
    expenses.value = expensesRes.data;
  } catch {
    error.value = "Erreur lors du chargement des budgets.";
  } finally {
    loading.value = false;
  }
};

const saveBudget = async () => {
  if (!selectedProjectId.value || !budgetForm.value.category || budgetForm.value.allocated_amount <= 0) {
    toast.error("Veuillez remplir tous les champs.");
    return;
  }
  try {
    if (budgetForm.value.id) {
      // Update
      await api.put(`/projects/${selectedProjectId.value}/budgets/${budgetForm.value.id}`, {
        category: budgetForm.value.category,
        allocated_amount: budgetForm.value.allocated_amount
      });
      toast.success('Budget modifié avec succès.');
    } else {
      // Create
      await api.post(`/projects/${selectedProjectId.value}/budgets/`, {
        category: budgetForm.value.category,
        allocated_amount: budgetForm.value.allocated_amount,
        currency: budgetForm.value.currency
      });
      toast.success('Budget créé avec succès.');
    }
    showBudgetModal.value = false;
    budgetForm.value = { id: null, category: '', allocated_amount: 0, currency: 'XOF' };
    await fetchBudgetData();
  } catch {
    toast.error('Erreur lors de la sauvegarde du budget.');
  }
};

const editBudget = (b: any) => {
  budgetForm.value = {
    id: b.id,
    category: b.category,
    allocated_amount: b.allocated_amount,
    currency: b.currency
  };
  showBudgetModal.value = true;
};

const deleteBudget = async (b: any) => {
  if (!selectedProjectId.value) return;
  if (!confirm(`Voulez-vous vraiment supprimer le budget "${b.category}" ?`)) return;
  try {
    await api.delete(`/projects/${selectedProjectId.value}/budgets/${b.id}`);
    toast.success('Budget supprimé avec succès.');
    await fetchBudgetData();
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail;
    toast.error(errorDetail || "Erreur lors de la suppression du budget.");
  }
};

const createExpense = async () => {
  if (!selectedProjectId.value || expenseForm.value.amount <= 0 || !expenseForm.value.date_incurred) {
    toast.error("Veuillez remplir les champs obligatoires.");
    return;
  }
  try {
    await api.post(`/projects/${selectedProjectId.value}/budgets/expenses`, expenseForm.value);
    showExpenseModal.value = false;
    expenseForm.value = { budget_id: null, amount: 0, date_incurred: '', description: '' };
    toast.success('Dépense enregistrée.');
    await fetchBudgetData();
  } catch (error:any) {
    const errorDetail = error.response?.data?.detail;
    toast.error(errorDetail || "Erreur lors de l'enregistrement de la dépense.");
  }
};

const updateExpenseStatus = async (expenseId: number, status: string) => {
  if (!selectedProjectId.value) return;
  try {
    await api.patch(`/projects/${selectedProjectId.value}/budgets/expenses/${expenseId}/status`, { status });
    toast.success(`Dépense ${status === 'Approved' ? 'approuvée' : 'rejetée'}.`);
    await fetchBudgetData();
  } catch {
    toast.error("Erreur lors de la mise à jour du statut.");
  }
};

watch(selectedProjectId, () => {
  fetchBudgetData();
});

onMounted(async () => {
  await fetchProjects();
  if (selectedProjectId.value) {
    await fetchBudgetData();
  }
});
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-8 w-full">
      
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Suivi du Budget Projet</h1>
          <p class="mt-1 text-gray-500">Gestion des budgets alloués et des dépenses</p>
        </div>
        <div class="flex gap-4 items-center">
          <select v-model="selectedProjectId" class="px-4 py-2 rounded-lg border border-gray-200 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-[#d10f2f] w-50">
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.code }} - {{ p.nom }}</option>
          </select>
          <button @click="showExpenseModal = true" :disabled="!selectedProjectId" class="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            Nouvelle Dépense
          </button>
          <button v-if="canManageBudget" @click="budgetForm = { id: null, category: '', allocated_amount: 0, currency: 'XOF' }; showBudgetModal = true" :disabled="!selectedProjectId" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            Ajouter un Budget
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
      </div>

      <div v-else-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg">
        {{ error }}
      </div>

      <div v-else-if="!selectedProjectId" class="text-center py-12 text-gray-500">Aucun projet disponible.</div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Budgets Table -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden h-max">
          <div class="p-6 border-b border-gray-100">
            <h2 class="text-xl font-bold text-gray-900">Lignes Budgétaires</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                <tr>
                  <th class="px-6 py-4 font-medium">Catégorie</th>
                  <th class="px-6 py-4 font-medium">Alloué</th>
                  <th class="px-6 py-4 font-medium">Consommé</th>
                  <th class="px-6 py-4 font-medium">Restant</th>
                  <th v-if="canManageBudget" class="px-6 py-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="b in budgets" :key="b.id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ b.category }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ b.allocated_amount }} {{ b.currency }}</td>
                  <td class="px-6 py-4 text-sm text-red-600">{{ b.consumed }} {{ b.currency }}</td>
                  <td class="px-6 py-4 text-sm font-bold text-green-600">{{ b.allocated_amount - b.consumed }} {{ b.currency }}</td>
                  <td v-if="canManageBudget" class="px-6 py-4 text-sm">
                    <div class="flex gap-2">
                      <button @click="editBudget(b)" class="text-blue-600 hover:text-blue-800" title="Modifier"><span class="material-symbols-outlined text-lg">edit</span></button>
                      <button @click="deleteBudget(b)" class="text-red-600 hover:text-red-800" title="Supprimer"><span class="material-symbols-outlined text-lg">delete</span></button>
                    </div>
                  </td>
                </tr>
                <tr v-if="budgets.length === 0">
                  <td :colspan="canManageBudget ? 5 : 4" class="px-6 py-8 text-center text-gray-500">Aucun budget défini.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Expenses Table -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="p-6 border-b border-gray-100">
            <h2 class="text-xl font-bold text-gray-900">Dernières Dépenses</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                <tr>
                  <th class="px-6 py-4 font-medium">Date</th>
                  <th class="px-6 py-4 font-medium">Description</th>
                  <th class="px-6 py-4 font-medium">Montant</th>
                  <th class="px-6 py-4 font-medium">Statut</th>
                  <th class="px-6 py-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="e in expenses" :key="e.id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-6 py-4 text-sm text-gray-500">{{ e.date_incurred }}</td>
                  <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ e.description || '-' }}</td>
                  <td class="px-6 py-4 text-sm font-bold text-gray-900">{{ e.amount }} XOF</td>
                  <td class="px-6 py-4">
                    <span :class="{'bg-green-100 text-green-800': e.status === 'Approved', 'bg-yellow-100 text-yellow-800': e.status === 'Pending', 'bg-red-100 text-red-800': e.status === 'Rejected'}" class="px-2 py-1 text-xs font-semibold rounded-full">
                      {{ e.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm">
                    <div v-if="e.status === 'Pending'" class="flex gap-2">
                      <button @click="updateExpenseStatus(e.id, 'Approved')" class="text-green-600 hover:text-green-800" title="Approuver"><span class="material-symbols-outlined text-lg">check_circle</span></button>
                      <button @click="updateExpenseStatus(e.id, 'Rejected')" class="text-red-600 hover:text-red-800" title="Rejeter"><span class="material-symbols-outlined text-lg">cancel</span></button>
                    </div>
                  </td>
                </tr>
                <tr v-if="expenses.length === 0">
                  <td colspan="5" class="px-6 py-8 text-center text-gray-500">Aucune dépense enregistrée.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Budget Creation/Edit Modal -->
      <div v-if="showBudgetModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-xl w-96 shadow-xl">
          <h2 class="text-xl font-bold mb-4 text-gray-900">{{ budgetForm.id ? 'Modifier le Budget' : 'Ajouter un Budget' }}</h2>
          <form @submit.prevent="saveBudget" class="space-y-3">
            <input v-model="budgetForm.category" placeholder="Catégorie (ex: Main d'oeuvre)" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            <input type="number" v-model.number="budgetForm.allocated_amount" min="1" placeholder="Montant alloué (XOF)" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            <div class="flex justify-end gap-2 mt-4">
              <button type="button" @click="showBudgetModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">Annuler</button>
              <button type="submit" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg">Enregistrer</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Expense Creation Modal -->
      <div v-if="showExpenseModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-xl w-96 shadow-xl">
          <h2 class="text-xl font-bold mb-4 text-gray-900">Nouvelle Dépense</h2>
          <form @submit.prevent="createExpense" class="space-y-3">
            <select v-model="expenseForm.budget_id" class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500">
              <option :value="null">Ligne budgétaire (optionnel)</option>
              <option v-for="b in budgets" :key="b.id" :value="b.id">{{ b.category }}</option>
            </select>
            <input type="number" v-model.number="expenseForm.amount" min="1" placeholder="Montant (XOF)" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            <div>
              <label class="block text-xs text-gray-500 mb-1">Date de la dépense</label>
              <input type="date" v-model="expenseForm.date_incurred" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            </div>
            <input v-model="expenseForm.description" placeholder="Description (optionnel)" class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            <div class="flex justify-end gap-2 mt-4">
              <button type="button" @click="showExpenseModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">Annuler</button>
              <button type="submit" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg">Enregistrer</button>
            </div>
          </form>
        </div>
      </div>
      
    </div>
  </AppLayout>
</template>
