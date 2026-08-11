<template>
  <AppLayout>
    <div class="max-w-5xl mx-auto space-y-8 w-full">
          
          <div class="flex justify-between items-center">
            <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span class="material-symbols-outlined text-[#d10f2f]">receipt_long</span>
              Pièce de Caisse
            </h1>
            <button 
              @click="generateCaissePdf"
              :disabled="isSubmitting"
              class="px-4 py-2 bg-[#d10f2f] text-white rounded-xl shadow-lg hover:bg-[#97091f] transition flex items-center gap-2 disabled:opacity-70"
            >
              <div v-if="isSubmitting" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
              <span v-else class="material-symbols-outlined">download</span>
              Générer et Enregistrer
            </button>
          </div>

          <!-- Formulaire de saisie -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-8">
            <!-- Entête -->
            <div class="grid grid-cols-4 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">NUM</label>
                <input v-model="form.num" type="text" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">N° AFFAIRE</label>
                <input v-model="form.affaire" type="text" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">N° CIA</label>
                <input v-model="form.cia" type="text" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">MOYEN DE PAIEMENT</label>
                <select v-model="form.payment_method" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                  <option value="">Sélectionner</option>
                  <option value="Transfert (Wave/Orange Money)">Transfert (Wave/Orange Money)</option>
                  <option value="Liquide">Liquide</option>
                  <option value="Chèque">Chèque</option>
                  <option value="Carte Bancaire">Carte Bancaire</option>
                </select>
              </div>
            </div>

            <!-- Dépenses -->
            <div>
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-800">Dépenses</h3>
                <button @click="addDepense" class="text-sm text-red-600 font-medium hover:text-red-800 flex items-center gap-1">
                  <span class="material-symbols-outlined text-sm">add</span> Ajouter une ligne
                </button>
              </div>
              <table class="w-full text-left text-sm text-gray-600">
                <thead class="bg-gray-50 text-gray-700">
                  <tr>
                    <th class="px-4 py-2 rounded-l-lg w-1/4">DATE</th>
                    <th class="px-4 py-2 w-1/2">DÉSIGNATION</th>
                    <th class="px-4 py-2">MONTANT</th>
                    <th class="px-4 py-2 rounded-r-lg w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in form.depenses" :key="'dep-'+index" class="border-b last:border-0">
                    <td class="py-2 pr-2"><input v-model="row.date" type="date" class="w-full px-3 py-1.5 border rounded-lg" /></td>
                    <td class="py-2 pr-2"><input v-model="row.designation" type="text" class="w-full px-3 py-1.5 border rounded-lg" placeholder="Description" /></td>
                    <td class="py-2 pr-2"><input v-model="row.montant" type="text" class="w-full px-3 py-1.5 border rounded-lg" placeholder="0 CFA" /></td>
                    <td class="py-2 text-right">
                      <button @click="removeDepense(index)" class="text-gray-400 hover:text-red-500"><span class="material-symbols-outlined text-lg">delete</span></button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <hr class="border-gray-100" />

            <!-- Recettes -->
            <div>
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-800">Recettes</h3>
                <button @click="addRecette" class="text-sm text-red-600 font-medium hover:text-red-800 flex items-center gap-1">
                  <span class="material-symbols-outlined text-sm">add</span> Ajouter une ligne
                </button>
              </div>
              <table class="w-full text-left text-sm text-gray-600">
                <thead class="bg-gray-50 text-gray-700">
                  <tr>
                    <th class="px-4 py-2 rounded-l-lg w-1/4">DATE</th>
                    <th class="px-4 py-2 w-1/2">DÉSIGNATION</th>
                    <th class="px-4 py-2">MONTANT</th>
                    <th class="px-4 py-2 rounded-r-lg w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in form.recettes" :key="'rec-'+index" class="border-b last:border-0">
                    <td class="py-2 pr-2"><input v-model="row.date" type="date" class="w-full px-3 py-1.5 border rounded-lg" /></td>
                    <td class="py-2 pr-2"><input v-model="row.designation" type="text" class="w-full px-3 py-1.5 border rounded-lg" placeholder="Description" /></td>
                    <td class="py-2 pr-2"><input v-model="row.montant" type="text" class="w-full px-3 py-1.5 border rounded-lg" placeholder="0 CFA" /></td>
                    <td class="py-2 text-right">
                      <button @click="removeRecette(index)" class="text-gray-400 hover:text-red-500"><span class="material-symbols-outlined text-lg">delete</span></button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Historique des pièces générées -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mt-8">
            <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
                <span class="material-symbols-outlined">history</span>
                Historique des Pièces
              </h2>
              <div class="relative">
                <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
                <input 
                  v-model="searchQuery" 
                  @input="debouncedSearch"
                  class="pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 transition-shadow w-64" 
                  placeholder="Rechercher..."
                >
              </div>
            </div>
            
            <div class="overflow-x-auto relative min-h-[200px]">
              <div v-if="loadingHistory" class="absolute inset-0 bg-white/50 flex justify-center items-center z-10 backdrop-blur-[1px]">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
              </div>
              <table class="w-full text-left">
                <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b">
                  <tr>
                    <th @click="sortBy('id')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                      <div class="flex items-center gap-1">ID <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'id'}">{{ sortColumn === 'id' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                    </th>
                    <th @click="sortBy('num')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                      <div class="flex items-center gap-1">NUM <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'num'}">{{ sortColumn === 'num' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                    </th>
                    <th @click="sortBy('affaire')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                      <div class="flex items-center gap-1">AFFAIRE <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'affaire'}">{{ sortColumn === 'affaire' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                    </th>
                    <th @click="sortBy('cia')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                      <div class="flex items-center gap-1">CIA <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'cia'}">{{ sortColumn === 'cia' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                    </th>
                    <th @click="sortBy('created_at')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                      <div class="flex items-center gap-1">Date <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'created_at'}">{{ sortColumn === 'created_at' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                    </th>
                    <th @click="sortBy('created_at')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                      <div class="flex items-center gap-1">Année <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'created_at'}">{{ sortColumn === 'created_at' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                    </th>
                    <th class="px-6 py-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="item in sortedHistory" :key="item.id" class="hover:bg-gray-50 transition-colors">
                    <td class="px-6 py-4 text-sm font-bold text-gray-900">PC-{{ item.id }}</td>
                    <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ item.num || '-' }}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">{{ item.affaire || '-' }}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">{{ item.cia || '-' }}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">{{ new Date(item.created_at).toLocaleDateString('fr-FR', { month: '2-digit', day: '2-digit' }) }}</td>
                    <td class="px-6 py-4 text-sm font-bold text-gray-700">{{ new Date(item.created_at).getFullYear() }}</td>
                    <td class="px-6 py-4 text-sm flex gap-3">
                      <a v-if="item.pdf_url" :href="item.pdf_url" target="_blank" class="text-indigo-600 hover:text-indigo-900 flex items-center gap-1 font-medium">
                        <span class="material-symbols-outlined text-[18px]">download</span> PDF
                      </a>
                      <button @click="openAttachments(item.id)" class="text-red-600 hover:text-red-900 flex items-center gap-1 font-medium">
                        <span class="material-symbols-outlined text-[18px]">attach_file</span> Photos
                      </button>
                    </td>
                  </tr>
                  <tr v-if="sortedHistory.length === 0">
                    <td colspan="7" class="px-6 py-8 text-center text-gray-500">Aucune pièce de caisse générée.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
    </div>
  </AppLayout>
  <VoucherAttachmentModal 
    :is-open="isAttachmentModalOpen"
    :voucher-id="selectedVoucherId"
    type="caisse"
    @close="isAttachmentModalOpen = false"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import VoucherAttachmentModal from '@/components/VoucherAttachmentModal.vue';
import { api } from '@/services/api';
import { useToast } from '@/composables/useToast';

const toast = useToast();
const isSubmitting = ref(false);

const form = ref({
  num: '',
  affaire: '',
  cia: '',
  payment_method: '',
  depenses: [{ date: '', designation: '', montant: '' }],
  recettes: [{ date: '', designation: '', montant: '' }]
});

const history = ref<any[]>([]);
const loadingHistory = ref(false);

const searchQuery = ref('');
let debounceTimer: any = null;

const sortColumn = ref('id');
const sortOrder = ref<'asc' | 'desc'>('desc');

const isAttachmentModalOpen = ref(false);
const selectedVoucherId = ref<number | null>(null);

const openAttachments = (id: number) => {
  selectedVoucherId.value = id;
  isAttachmentModalOpen.value = true;
};

const addDepense = () => form.value.depenses.push({ date: '', designation: '', montant: '' });
const removeDepense = (index: number) => form.value.depenses.splice(index, 1);

const addRecette = () => form.value.recettes.push({ date: '', designation: '', montant: '' });
const removeRecette = (index: number) => form.value.recettes.splice(index, 1);

async function fetchHistory() {
  loadingHistory.value = true;
  try {
    const searchParam = searchQuery.value ? `?search=${encodeURIComponent(searchQuery.value)}` : '';
    const res = await api.get(`/caisse/${searchParam}`);
    history.value = res.data;
  } catch (e) {
    console.error("Erreur lors de la récupération de l'historique", e);
  } finally {
    loadingHistory.value = false;
  }
}

const debouncedSearch = () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchHistory();
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

const sortedHistory = computed(() => {
  return [...history.value].sort((a, b) => {
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

async function generateCaissePdf() {
  isSubmitting.value = true;
  try {
    const res = await api.post('/caisse/generate', form.value);
    toast.success("Pièce de caisse générée et enregistrée avec succès !");
    
    await fetchHistory();

    form.value = {
      num: '',
      affaire: '',
      cia: '',
      depenses: [{ date: '', designation: '', montant: '' }],
      recettes: [{ date: '', designation: '', montant: '' }]
    };

    if (res.data && res.data.pdf_url) {
      const url = res.data.pdf_url;
      window.open(url, '_blank');
    }
  } catch (e) {
    console.error("Erreur lors de la génération", e);
    toast.error("Une erreur est survenue lors de la génération du PDF.");
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(() => {
  fetchHistory();
});
</script>
