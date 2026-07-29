<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import AppLayout from "@/layouts/AppLayout.vue";
import api from "@/services/api";
import { StockService } from '@/services/stock';
import { useToast } from '@/composables/useToast';
import { getStoredProfile } from '@/services/session';

const toast = useToast();

const reservations = ref<any[]>([]);
const projects = ref<any[]>([]);
const products = ref<any[]>([]);
const tasks = ref<any[]>([]);

const loading = ref(true);
const error = ref<string | null>(null);

const showModal = ref(false);
const isSubmitting = ref(false);

const searchQuery = ref('');
let debounceTimer: any = null;

const sortColumn = ref('id');
const sortOrder = ref<'asc' | 'desc'>('desc');

const form = ref({
  project_id: '',
  task_id: '',
  product_id: '',
  quantity: 1
});

const fetchData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const searchParam = searchQuery.value ? `?search=${encodeURIComponent(searchQuery.value)}` : '';
    const [resData, projData, prodData] = await Promise.all([
      api.get(`/stock-reservations/${searchParam}`),
      api.get('/projects/'),
      StockService.getProducts()
    ]);
    
    reservations.value = resData.data;
    projects.value = projData.data;
    products.value = prodData.data;
  } catch (err: any) {
    error.value = "Erreur lors du chargement des données.";
  } finally {
    loading.value = false;
  }
};

import { watch } from 'vue';

watch(() => form.value.project_id, async (newVal) => {
  if (newVal) {
    try {
      const res = await api.get(`/projects/${newVal}/tasks`);
      tasks.value = res.data || [];
    } catch {
      tasks.value = [];
    }
  } else {
    tasks.value = [];
  }
  form.value.task_id = '';
});

const debouncedSearch = () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchData();
  }, 300);
};

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortOrder.value = 'asc';
  }
};

const sortedReservations = computed(() => {
  return [...reservations.value].sort((a, b) => {
    let valA = a[sortColumn.value];
    let valB = b[sortColumn.value];

    if (valA === null || valA === undefined) valA = '';
    if (valB === null || valB === undefined) valB = '';

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const createReservation = async () => {
  if (!form.value.project_id || !form.value.product_id || form.value.quantity < 1) {
    toast.error("Veuillez remplir tous les champs correctement.");
    return;
  }

  isSubmitting.value = true;
  try {
    await api.post('/stock-reservations/', {
      project_id: Number(form.value.project_id),
      product_id: Number(form.value.product_id),
      task_id: form.value.task_id ? Number(form.value.task_id) : null,
      quantity: form.value.quantity,
      reserved_by_id: null
    });
    
    toast.success("Réservation créée avec succès !");
    showModal.value = false;
    form.value = { project_id: '', task_id: '', product_id: '', quantity: 1 };
    await fetchData();
  } catch (err: any) {
    const msg = err.response?.data?.detail || "Erreur lors de la création de la réservation.";
    toast.error(msg);
  } finally {
    isSubmitting.value = false;
  }
};

const consumeReservation = async (reservationId: number) => {
  try {
    await api.post(`/stock-reservations/${reservationId}/consume`);
    toast.success("Réservation consommée !");
    await fetchData();
  } catch (err: any) {
    const msg = err.response?.data?.detail || "Erreur lors de la consommation.";
    toast.error(msg);
  }
};

const approveReservation = async (reservationId: number) => {
  try {
    await api.post(`/stock-reservations/${reservationId}/approve`);
    toast.success("Réservation approuvée avec succès !");
    await fetchData();
  } catch (err: any) {
    const msg = err.response?.data?.detail || "Erreur lors de l'approbation.";
    toast.error(msg);
  }
};

const rejectReservation = async (reservationId: number) => {
  try {
    await api.post(`/stock-reservations/${reservationId}/reject`);
    toast.success("Réservation rejetée et stock restitué !");
    await fetchData();
  } catch (err: any) {
    const msg = err.response?.data?.detail || "Erreur lors du rejet.";
    toast.error(msg);
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-8 w-full">
      
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Réservations de Stock</h1>
          <p class="mt-1 text-gray-500">Gérer les réservations d'articles pour les projets</p>
        </div>
        <div class="flex gap-4">
          <button @click="showModal = true" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
            <span class="material-symbols-outlined text-sm">add</span>
            Nouvelle Réservation
          </button>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
        <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 class="text-xl font-bold text-gray-900">
            Liste des Réservations
          </h2>
          <div class="relative">
            <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
            <input 
              v-model="searchQuery" 
              @input="debouncedSearch"
              class="pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 transition-shadow w-64" 
              placeholder="Rechercher réservation..."
            >
          </div>
        </div>

        <div v-if="loading && !reservations.length" class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
        </div>

        <div v-else-if="error" class="bg-red-50 text-red-600 p-4 m-4 rounded-lg">
          {{ error }}
        </div>

        <div v-else class="overflow-x-auto relative min-h-[200px]">
          <div v-if="loading" class="absolute inset-0 bg-white/50 flex justify-center items-center z-10 backdrop-blur-[1px]">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
          </div>
          <table class="w-full text-left">
            <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
              <tr>
                <th @click="sortBy('id')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">ID Réservation <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'id'}">{{ sortColumn === 'id' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('project_id')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">Projet <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'project_id'}">{{ sortColumn === 'project_id' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('product_name')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">Produit <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'product_name'}">{{ sortColumn === 'product_name' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('quantity')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">Quantité <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'quantity'}">{{ sortColumn === 'quantity' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('created_at')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">Date <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'created_at'}">{{ sortColumn === 'created_at' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('created_at')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">Année <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'created_at'}">{{ sortColumn === 'created_at' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('status')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                  <div class="flex items-center gap-1">Statut <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'status'}">{{ sortColumn === 'status' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th class="px-6 py-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="res in sortedReservations" :key="res.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 text-sm font-bold text-gray-900">RES-{{ res.id }}</td>
                <td class="px-6 py-4 text-sm text-gray-500">#{{ res.project_id }}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ res.product_name || `Produit #${res.product_id}` }}</td>
                <td class="px-6 py-4 text-sm font-bold text-gray-900">{{ res.quantity }}</td>
                <td class="px-6 py-4 text-sm text-gray-500">{{ new Date(res.created_at).toLocaleDateString('fr-FR', { month: '2-digit', day: '2-digit' }) }}</td>
                <td class="px-6 py-4 text-sm font-bold text-gray-700">
                  <div class="flex flex-col">
                    <span>{{ new Date(res.created_at).getFullYear() }}</span>
                    <span v-if="res.task_id" class="text-xs text-blue-600">Tâche #{{ res.task_id }}</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span 
                    :class="{
                      'bg-green-100 text-green-800': res.status === 'Approved',
                      'bg-blue-100 text-blue-800': res.status === 'Consumed',
                      'bg-yellow-100 text-yellow-800': res.status === 'Pending',
                      'bg-red-100 text-red-800': res.status === 'Cancelled'
                    }" 
                    class="px-2 py-1 text-xs font-semibold rounded-full"
                  >
                    {{ res.status }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm">
                  <div v-if="res.status === 'Pending'" class="flex items-center gap-2">
                    <button 
                      @click="approveReservation(res.id)"
                      class="text-green-600 hover:underline font-medium"
                    >
                      Approuver
                    </button>
                    <span class="text-gray-300">|</span>
                    <button 
                      @click="rejectReservation(res.id)"
                      class="text-red-600 hover:underline font-medium"
                    >
                      Rejeter
                    </button>
                  </div>
                  <button 
                    v-else-if="res.status === 'Approved'"
                    @click="consumeReservation(res.id)"
                    class="text-blue-600 hover:underline font-medium"
                  >
                    Consommer
                  </button>
                  <span v-else-if="res.status === 'Consumed'" class="text-gray-400">Consommée</span>
                  <span v-else-if="res.status === 'Cancelled'" class="text-red-400">Annulée</span>
                </td>
              </tr>
              <tr v-if="sortedReservations.length === 0">
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">Aucune réservation de stock trouvée.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
    </div>

    <!-- Nouvelle Réservation Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-full max-w-md shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Nouvelle Réservation</h2>
        <form @submit.prevent="createReservation" class="space-y-4">
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Projet</label>
            <select v-model="form.project_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500">
              <option value="" disabled>Sélectionner un projet</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.code }} - {{ p.nom }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tâche (Optionnel)</label>
            <select v-model="form.task_id" :disabled="!form.project_id" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500 disabled:bg-gray-100">
              <option value="">-- Sans tâche --</option>
              <option v-for="t in tasks" :key="t.id" :value="t.id">{{ t.title }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Produit</label>
            <select v-model="form.product_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500">
              <option value="" disabled>Sélectionner un produit</option>
              <option v-for="prod in products" :key="prod.id" :value="prod.id">{{ prod.designation || prod.name }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Quantité</label>
            <input type="number" v-model.number="form.quantity" min="1" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500" />
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <button type="button" @click="showModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors">
              Annuler
            </button>
            <button type="submit" :disabled="isSubmitting" class="px-4 py-2 bg-[#d10f2f] hover:bg-[#97091f] text-white rounded-lg font-medium transition-colors disabled:opacity-70 flex items-center justify-center min-w-[120px]">
              <div v-if="isSubmitting" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
              <span v-else>Réserver</span>
            </button>
          </div>
        </form>
      </div>
    </div>

  </AppLayout>
</template>
