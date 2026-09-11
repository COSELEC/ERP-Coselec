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

          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-8">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">DATE</label>
                <input v-model="form.date" type="date" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
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
              <div class="col-span-2 md:col-span-4">
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
                    <th class="px-3 py-2 rounded-l-lg w-10 text-xs">N°</th>
                    <th class="px-3 py-2 w-2/5 text-xs">DÉSIGNATION</th>
                    <th class="px-3 py-2 text-xs">QUANTITÉ</th>
                    <th class="px-3 py-2 text-xs">PRIX UNITAIRE</th>
                    <th class="px-3 py-2 text-xs">MONTANT TOTAL</th>
                    <th class="px-3 py-2 rounded-r-lg w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in form.depenses" :key="'dep-'+index" class="border-b last:border-0">
                    <td class="py-2 pr-2 text-xs text-gray-400 font-medium">{{ index + 1 }}</td>
                    <td class="py-2 pr-2">
                      <textarea v-model="row.designation" rows="2" class="w-full px-2 py-1 border border-gray-200 rounded-lg text-sm resize-none" placeholder="Désignation..." style="word-break:break-word;white-space:pre-wrap;"></textarea>
                    </td>
                    <td class="py-2 pr-2"><input v-model.number="row.quantite" type="number" min="0" class="w-20 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="1" /></td>
                    <td class="py-2 pr-2"><input v-model.number="row.prix_unitaire" type="number" min="0" class="w-24 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="0 CFA" /></td>
                    <td class="py-2 pr-2 font-semibold text-gray-900 whitespace-nowrap">{{ ((row.quantite || 0) * (row.prix_unitaire || 0)).toLocaleString('fr-FR') }} CFA</td>
                    <td class="py-2 text-right">
                      <button @click="removeDepense(index)" class="text-gray-400 hover:text-red-500"><span class="material-symbols-outlined text-lg">delete</span></button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <hr class="border-gray-100" />

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
                    <th class="px-3 py-2 rounded-l-lg w-10 text-xs">N°</th>
                    <th class="px-3 py-2 w-2/5 text-xs">DÉSIGNATION</th>
                    <th class="px-3 py-2 text-xs">QUANTITÉ</th>
                    <th class="px-3 py-2 text-xs">PRIX UNITAIRE</th>
                    <th class="px-3 py-2 text-xs">MONTANT TOTAL</th>
                    <th class="px-3 py-2 rounded-r-lg w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in form.recettes" :key="'rec-'+index" class="border-b last:border-0">
                    <td class="py-2 pr-2 text-xs text-gray-400 font-medium">{{ index + 1 }}</td>
                    <td class="py-2 pr-2">
                      <textarea v-model="row.designation" rows="2" class="w-full px-2 py-1 border border-gray-200 rounded-lg text-sm resize-none" placeholder="Désignation..." style="word-break:break-word;white-space:pre-wrap;"></textarea>
                    </td>
                    <td class="py-2 pr-2"><input v-model.number="row.quantite" type="number" min="0" class="w-20 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="1" /></td>
                    <td class="py-2 pr-2"><input v-model.number="row.prix_unitaire" type="number" min="0" class="w-24 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="0 CFA" /></td>
                    <td class="py-2 pr-2 font-semibold text-gray-900 whitespace-nowrap">{{ ((row.quantite || 0) * (row.prix_unitaire || 0)).toLocaleString('fr-FR') }} CFA</td>
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
                    <td class="px-6 py-4 text-sm text-gray-500">{{ formatMonthDay(item.created_at) }}</td>
                    <td class="px-6 py-4 text-sm font-bold text-gray-700">{{ formatYear(item.created_at) }}</td>
                    <td class="px-6 py-4 text-sm flex flex-wrap gap-3 items-center">
                      <a v-if="item.pdf_url" :href="item.pdf_url" target="_blank" class="text-indigo-600 hover:text-indigo-900 flex items-center gap-1 font-medium">
                        <span class="material-symbols-outlined text-[18px]">download</span> PDF
                      </a>
                      <button @click="openAttachments(item.id)" class="text-red-600 hover:text-red-900 flex items-center gap-1 font-medium">
                        <span class="material-symbols-outlined text-[18px]">attach_file</span> Photos
                      </button>
                      
                      <!-- Validation Buttons -->
                      <button 
                        v-if="canValidateCG && !item.validator_cg_id"
                        @click="validateCaisse(item.id, 'cg')" 
                        class="px-2 py-1 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded text-xs font-semibold flex items-center gap-1 transition-colors"
                      >
                        <span class="material-symbols-outlined text-[14px]">check_circle</span> Viser CG
                      </button>
                      <button 
                        v-if="canValidateDirection && !item.validator_dga_id"
                        @click="validateCaisse(item.id, 'dga')" 
                        class="px-2 py-1 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded text-xs font-semibold flex items-center gap-1 transition-colors"
                      >
                        <span class="material-symbols-outlined text-[14px]">check_circle</span> Viser DGA
                      </button>
                      <button 
                        v-if="canValidateDirection && !item.validator_dg_id"
                        @click="validateCaisse(item.id, 'dg')" 
                        class="px-2 py-1 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded text-xs font-semibold flex items-center gap-1 transition-colors"
                      >
                        <span class="material-symbols-outlined text-[14px]">check_circle</span> Viser DG
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
    :is-open="attachmentModal.isOpen.value"
    :voucher-id="attachmentModal.selectedItem.value"
    type="caisse"
    @close="attachmentModal.close()"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import VoucherAttachmentModal from '@/components/VoucherAttachmentModal.vue';
import { api } from '@/services/api';
import { useToast, useFormatters, useTableSort, useDebounceFn, useModal } from '@/composables';
import { getStoredProfile } from '@/services/session';

const toast = useToast();
const { formatMonthDay, formatYear } = useFormatters();
const attachmentModal = useModal<number>();
const isSubmitting = ref(false);

const profile = getStoredProfile();
const userRoles = profile ? profile.roles : [];

const canValidateCG = userRoles.includes('RH / Comptabilité') || userRoles.includes('Admin');
const canValidateDirection = userRoles.includes('Direction') || userRoles.includes('Admin');

const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const form = ref({
  date: todayStr(),
  num: '',
  affaire: '',
  cia: '',
  payment_method: '',
  depenses: [{ designation: '', quantite: 1, prix_unitaire: 0 }] as Array<{designation: string; quantite: number; prix_unitaire: number}>,
  recettes: [{ designation: '', quantite: 1, prix_unitaire: 0 }] as Array<{designation: string; quantite: number; prix_unitaire: number}>
});

const history = ref<any[]>([]);
const loadingHistory = ref(false);
const searchQuery = ref('');

const { sortColumn, sortOrder, sortBy, sortedItems: sortedHistory } = useTableSort(history, 'id', 'desc');

const openAttachments = (id: number) => {
  attachmentModal.open(id);
};

const addDepense = () => form.value.depenses.push({ designation: '', quantite: 1, prix_unitaire: 0 });
const removeDepense = (index: number) => form.value.depenses.splice(index, 1);

const addRecette = () => form.value.recettes.push({ designation: '', quantite: 1, prix_unitaire: 0 });
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

const { debounced: debouncedSearch } = useDebounceFn(fetchHistory, 300);

async function generateCaissePdf() {
  isSubmitting.value = true;
  try {
    // Transformer le format frontal vers le format backend
    const payload = {
      ...form.value,
      depenses: form.value.depenses.map((r: any, idx: number) => ({
        date: form.value.date,
        designation: r.designation,
        montant: ((r.quantite || 0) * (r.prix_unitaire || 0)).toString(),
        num: String(idx + 1)
      })),
      recettes: form.value.recettes.map((r: any, idx: number) => ({
        date: form.value.date,
        designation: r.designation,
        montant: ((r.quantite || 0) * (r.prix_unitaire || 0)).toString(),
        num: String(idx + 1)
      }))
    };
    const res = await api.post('/caisse/generate', payload);
    toast.success("Pièce de caisse générée et enregistrée avec succès !");
    
    await fetchHistory();

    form.value = {
      date: todayStr(),
      num: '',
      affaire: '',
      cia: '',
      payment_method: '',
      depenses: [{ designation: '', quantite: 1, prix_unitaire: 0 }] as any,
      recettes: [{ designation: '', quantite: 1, prix_unitaire: 0 }] as any
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

async function validateCaisse(id: number, role: string) {
  try {
    await api.post(`/caisse/${id}/validate/${role}`);
    toast.success("Pièce de caisse validée et signée avec succès.");
    await fetchHistory();
  } catch (e: any) {
    console.error("Erreur lors de la validation", e);
    toast.error(e.response?.data?.detail || "Erreur lors de la validation.");
  }
}

onMounted(() => {
  fetchHistory();
});
</script>
