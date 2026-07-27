<template>
  <AppLayout>
    <div class="max-w-6xl mx-auto space-y-8 w-full pb-12">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <span class="material-symbols-outlined text-[#d10f2f] text-4xl">account_balance</span>
            Pièce de Banque
          </h2>
          <p class="text-gray-500 mt-1">Créez une nouvelle pièce de banque liée à une pièce de caisse validée.</p>
        </div>
      </div>
      
      <form @submit.prevent="submitVoucher" class="space-y-8">
        
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
          <div class="flex items-center gap-2 mb-6 pb-4 border-b border-gray-100">
            <span class="material-symbols-outlined text-[#d10f2f]">info</span>
            <h3 class="text-lg font-bold text-gray-900">Informations Générales</h3>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Numéro d'ordre</label>
              <input :value="form.id || 'Chargement...'" type="text" disabled class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 text-gray-900 rounded-xl cursor-not-allowed font-bold" />
            </div>
            


            <div>
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Banque *</label>
              <input v-model="form.bank_name" type="text" required class="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" placeholder="Ex: BIS" />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">N° Chèque *</label>
              <input v-model="form.check_number" type="text" required class="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" placeholder="Ex: 00001077" />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Date *</label>
              <input v-model="form.date" type="date" required readonly class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 text-gray-600 rounded-xl cursor-not-allowed focus:outline-none" />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Période (MMYY) *</label>
              <input v-model="form.period_num" type="text" required readonly class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 text-gray-600 rounded-xl cursor-not-allowed font-bold focus:outline-none" />
            </div>

            <div class="lg:col-span-2">
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Bénéficiaire *</label>
              <input v-model="form.recipient" type="text" required class="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" placeholder="Ex: AU PORTEUR" />
            </div>

            <div class="lg:col-span-4">
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Libellé de la dépense *</label>
              <input v-model="form.description" type="text" required class="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" placeholder="Ex: AVANCE 50% / DEPLACEMENT COMASEL" />
            </div>

            <div class="lg:col-span-4">
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Lier à des pièces de caisse (Optionnel)</label>
              
              <!-- Custom Multi-Select -->
              <div class="relative">
                <div 
                  @click="isDropdownOpen = !isDropdownOpen" 
                  class="w-full min-h-[46px] px-4 py-2 bg-white border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-[#d10f2f]/20 focus-within:border-[#d10f2f] transition-all cursor-pointer flex flex-wrap gap-2 items-center"
                >
                  <div v-if="form.linked_caisse_voucher_ids.length === 0" class="text-gray-400">
                    Sélectionner des pièces de caisse...
                  </div>
                  
                  <span 
                    v-for="id in form.linked_caisse_voucher_ids" 
                    :key="id"
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#fff5f6] text-[#d10f2f] text-sm font-semibold border border-[#ffe0e4]"
                  >
                    PC-{{ id }}
                    <span @click.stop="toggleCaisseSelection(id)" class="material-symbols-outlined text-[14px] cursor-pointer hover:text-red-800">close</span>
                  </span>
                  
                  <span class="material-symbols-outlined ml-auto text-gray-400 transition-transform" :class="{'rotate-180': isDropdownOpen}">expand_more</span>
                </div>

                <!-- Invisible overlay to detect outside clicks -->
                <div v-if="isDropdownOpen" class="fixed inset-0 z-10" @click="isDropdownOpen = false"></div>

                <!-- Dropdown Menu -->
                <div 
                  v-if="isDropdownOpen" 
                  class="absolute z-20 w-full mt-2 bg-white border border-gray-100 rounded-xl shadow-xl max-h-60 overflow-y-auto"
                >
                  <div 
                    v-for="caisse in availableCaisseVouchers" 
                    :key="caisse.id"
                    @click="toggleCaisseSelection(caisse.id)"
                    class="px-4 py-3 flex items-center gap-3 hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0"
                  >
                    <div 
                      class="w-5 h-5 rounded border flex items-center justify-center transition-colors"
                      :class="form.linked_caisse_voucher_ids.includes(caisse.id) ? 'bg-[#d10f2f] border-[#d10f2f]' : 'border-gray-300 bg-white'"
                    >
                      <span v-if="form.linked_caisse_voucher_ids.includes(caisse.id)" class="material-symbols-outlined text-white text-[14px]">check</span>
                    </div>
                    <div>
                      <div class="font-bold text-gray-900">PC-{{ caisse.id }} <span class="text-gray-400 font-normal">| Num: {{ caisse.num || '-' }}</span></div>
                      <div class="text-xs text-gray-500">Affaire: {{ caisse.affaire || '-' }} | Montant: {{ caisse.total_amount || '0' }} {{ form.currency }}</div>
                    </div>
                  </div>
                  
                  <div v-if="availableCaisseVouchers.length === 0" class="px-4 py-8 text-center text-gray-500 text-sm">
                    Aucune pièce de caisse validée disponible.
                  </div>
                </div>
              </div>
              <p class="text-xs text-gray-500 mt-2">Permet de regrouper les documents d'un même ordre.</p>
            </div>
          </div>
        </div>

        <!-- Montants Card -->
        <div class="bg-gradient-to-br from-[#fff5f6] to-white p-8 rounded-2xl shadow-sm border border-[#ffe0e4]">
          <div class="flex items-center gap-2 mb-6 pb-4 border-b border-[#ffe0e4]">
            <span class="material-symbols-outlined text-[#d10f2f]">payments</span>
            <h3 class="text-lg font-bold text-gray-900">Détails du Montant</h3>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <label class="block text-xs font-semibold text-[#d10f2f] uppercase tracking-wider mb-1">Montant du Chèque (Chiffres) *</label>
              <div class="relative">
                <input v-model.number="form.amount_in_numbers" type="number" min="1" required class="w-full px-5 py-4 text-2xl bg-white border border-[#ffe0e4] rounded-xl focus:ring-4 focus:ring-[#d10f2f]/10 focus:border-[#d10f2f] pr-20 font-bold text-gray-900 transition-all shadow-sm" />
                <div class="absolute inset-y-0 right-0 flex items-center pr-5 pointer-events-none text-[#d10f2f] font-black text-xl">
                  {{ form.currency }}
                </div>
              </div>
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">Montant (Lettres) *</label>
              <input v-model="form.amount_in_letters" type="text" required class="w-full px-5 py-4 text-lg bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-[#d10f2f]/10 focus:border-[#d10f2f] font-medium text-gray-700 transition-all shadow-sm" placeholder="Saisir le montant en toutes lettres..." />
            </div>
          </div>
        </div>

        <!-- Imputations Analytiques Card -->
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
          <div class="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-[#d10f2f]">account_tree</span>
              <h3 class="text-lg font-bold text-gray-900">Imputations Analytiques</h3>
            </div>
            <button type="button" @click="addAllocation" class="px-4 py-2 bg-[#fff5f6] text-[#d10f2f] rounded-lg text-sm font-bold hover:bg-[#ffe0e4] transition-colors flex items-center gap-1 border border-[#ffe0e4]">
              <span class="material-symbols-outlined text-sm">add</span> Ajouter une ligne
            </button>
          </div>
          
          <div class="overflow-x-auto rounded-xl border border-gray-200">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-gray-50 text-gray-600">
                <tr>
                  <th class="px-4 py-3 font-bold uppercase text-xs tracking-wider border-b">Code Centre</th>
                  <th class="px-4 py-3 font-bold uppercase text-xs tracking-wider border-b">Désignation</th>
                  <th class="px-4 py-3 font-bold uppercase text-xs tracking-wider border-b">Client</th>
                  <th class="px-4 py-3 font-bold uppercase text-xs tracking-wider border-b">Compte Ana.</th>
                  <th class="px-4 py-3 font-bold uppercase text-xs tracking-wider border-b text-right">Montant</th>
                  <th class="px-4 py-3 font-bold uppercase text-xs tracking-wider border-b text-center w-16"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="(alloc, index) in form.allocations" :key="index" class="group hover:bg-gray-50/50 transition-colors">
                  <td class="p-2"><input v-model="alloc.cost_center_code" type="text" required class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" /></td>
                  <td class="p-2"><input v-model="alloc.cost_center_name" type="text" required class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" /></td>
                  <td class="p-2"><input v-model="alloc.client" type="text" class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all" /></td>
                  <td class="p-2">
                    <select v-model="alloc.analytical_account" required class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all font-medium text-gray-700">
                      <option value="" disabled>Sélectionner...</option>
                      <option value="DEPLAC">DEPLAC</option>
                      <option value="ASSUR">ASSUR</option>
                      <option value="FINAN">FINAN</option>
                      <option value="ACHAT">ACHAT</option>
                      <option value="AUTRE">AUTRE</option>
                    </select>
                  </td>
                  <td class="p-2"><input v-model.number="alloc.amount" type="number" min="0" required class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] transition-all text-right font-bold text-[#d10f2f]" /></td>
                  <td class="p-2 text-center">
                    <button type="button" @click="removeAllocation(index)" class="text-gray-400 hover:text-[#d10f2f] p-1.5 rounded-lg hover:bg-[#fff5f6] transition-all" title="Supprimer">
                      <span class="material-symbols-outlined text-lg block">delete</span>
                    </button>
                  </td>
                </tr>
                <tr v-if="form.allocations.length === 0">
                  <td colspan="6" class="px-6 py-12 text-center text-gray-500 bg-gray-50/50">
                    <span class="material-symbols-outlined text-4xl text-gray-300 mb-2 block">receipt_long</span>
                    Aucune imputation. Vous devez ventiler le montant du chèque.
                  </td>
                </tr>
              </tbody>
              <tfoot class="bg-gray-50">
                <tr>
                  <td colspan="4" class="px-6 py-4 text-right text-gray-600 font-bold uppercase text-xs tracking-wider">TOTAL IMPUTATIONS</td>
                  <td class="px-4 py-4 text-right text-xl font-black" :class="isTotalMatching ? 'text-green-600' : 'text-[#d10f2f]'">
                    {{ totalAllocation.toLocaleString() }} <span class="text-sm font-bold">{{ form.currency }}</span>
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
          
          <!-- Validation Réactive -->
          <div v-if="!isTotalMatching && form.amount_in_numbers > 0 && form.allocations.length > 0" class="mt-6 p-5 bg-[#fff5f6] border border-[#ffe0e4] rounded-xl flex items-start gap-4 shadow-sm animate-pulse-once">
            <div class="bg-white p-2 rounded-full shadow-sm text-[#d10f2f]">
              <span class="material-symbols-outlined block">warning</span>
            </div>
            <div>
              <strong class="block text-[#d10f2f] text-base mb-1">Déséquilibre financier détecté</strong>
              <p class="text-[#d10f2f]/80 text-sm">Le total des imputations (<strong>{{ totalAllocation.toLocaleString() }}</strong>) doit correspondre exactement au chèque (<strong>{{ form.amount_in_numbers.toLocaleString() }}</strong>).</p>
              <p class="text-[#d10f2f] font-bold mt-2 text-sm bg-white inline-block px-3 py-1 rounded-md shadow-sm border border-[#ffe0e4]">
                Écart à corriger : {{ Math.abs(form.amount_in_numbers - totalAllocation).toLocaleString() }} {{ form.currency }}
              </p>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end pt-4">
          <button type="submit" :disabled="!isFormValid" :class="['px-8 py-4 rounded-xl text-white font-bold text-lg flex items-center gap-3 transition-all', isFormValid ? 'bg-[#d10f2f] hover:bg-[#97091f] shadow-lg shadow-[#d10f2f]/30 hover:shadow-xl hover:shadow-[#d10f2f]/40 hover:-translate-y-0.5' : 'bg-gray-300 cursor-not-allowed shadow-none']">
            <span class="material-symbols-outlined">description</span>
            Générer la Pièce de Banque
          </button>
        </div>
      </form>
    <!-- History Section -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mt-8">
      <div class="p-6 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-gray-500">history</span>
          <h3 class="text-lg font-bold text-gray-900">Historique des Pièces de Banque</h3>
        </div>
        
        <div class="relative w-64">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Rechercher (Num, Banque...)" 
            class="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f]/20 focus:border-[#d10f2f] text-sm transition-all"
            @input="fetchHistory"
          />
          <span class="material-symbols-outlined absolute left-3 top-2 text-gray-400 text-[18px]">search</span>
        </div>
      </div>
      
      <div class="overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="bg-gray-50 text-gray-600 border-b border-gray-100">
            <tr>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider cursor-pointer hover:bg-gray-100 transition-colors" @click="toggleSort('id')">
                Numéro d'ordre
                <span v-if="sortColumn === 'id'" class="material-symbols-outlined text-[14px] align-middle">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span>
              </th>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider">Banque & Chèque</th>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider">Bénéficiaire</th>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider">Montant</th>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider">Pièces de Caisse</th>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider">Date</th>
              <th class="px-6 py-4 font-bold uppercase text-xs tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="item in sortedHistory" :key="item.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-6 py-4 font-bold text-gray-900">PB-{{ item.id }}</td>
              <td class="px-6 py-4">
                <div class="font-bold text-gray-900">{{ item.bank_name }}</div>
                <div class="text-xs text-gray-500">Chèque: {{ item.check_number }}</div>
              </td>
              <td class="px-6 py-4 text-sm text-gray-700 font-medium">{{ item.recipient }}</td>
              <td class="px-6 py-4 text-sm font-bold text-[#d10f2f]">{{ item.amount_in_numbers.toLocaleString() }} {{ item.currency }}</td>
              <td class="px-6 py-4">
                <div v-if="item.linked_caisse_voucher_ids && item.linked_caisse_voucher_ids.length > 0" class="flex flex-wrap gap-1">
                  <span 
                    v-for="cId in item.linked_caisse_voucher_ids" 
                    :key="cId"
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-[#fff5f6] text-[#d10f2f] border border-[#ffe0e4]"
                  >
                    PC-{{ cId }}
                  </span>
                </div>
                <span v-else class="text-gray-400 text-xs italic">-</span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-500">{{ new Date(item.created_at || item.date).toLocaleDateString('fr-FR') }}</td>
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
              <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                <span class="material-symbols-outlined text-4xl text-gray-300 mb-2 block">history</span>
                Aucune pièce générée
              </td>
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
    type="bank"
    @close="isAttachmentModalOpen = false"
  />
</template>

<script setup>
import { reactive, computed, onMounted, ref } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import VoucherAttachmentModal from '@/components/VoucherAttachmentModal.vue';
import { api } from '@/services/api';

const isAttachmentModalOpen = ref(false);
const selectedVoucherId = ref(null);
const isDropdownOpen = ref(false);

const openAttachments = (id) => {
  selectedVoucherId.value = id;
  isAttachmentModalOpen.value = true;
};

const toggleCaisseSelection = (id) => {
  const index = form.linked_caisse_voucher_ids.indexOf(id);
  if (index > -1) {
    form.linked_caisse_voucher_ids.splice(index, 1);
  } else {
    form.linked_caisse_voucher_ids.push(id);
  }
};

const form = reactive({
  id: null,
  bank_name: '',
  check_number: '',
  date: new Date().toISOString().split('T')[0],
  period_num: '',
  description: '',
  recipient: 'AU PORTEUR',
  amount_in_numbers: 0,
  currency: 'FCFA',
  amount_in_letters: '',
  allocations: [
    { cost_center_code: '', cost_center_name: '', client: '', analytical_account: '', amount: 0 }
  ],
  linked_caisse_voucher_ids: []
});

const availableCaisseVouchers = ref([]);
const history = ref([]);
const searchQuery = ref('');
const sortColumn = ref('id');
const sortOrder = ref('desc');

const sortedHistory = computed(() => {
  return [...history.value].sort((a, b) => {
    let valA = a[sortColumn.value];
    let valB = b[sortColumn.value];
    
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const toggleSort = (col) => {
  if (sortColumn.value === col) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = col;
    sortOrder.value = 'desc';
  }
};

const updatePeriod = () => {
  const d = new Date(form.date);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = String(d.getFullYear()).slice(2);
  form.period_num = `${month}${year}`;
};

const fetchNextId = async () => {
  try {
    const res = await api.get('/bank-vouchers/next-id');
    form.id = res.data.next_id;
  } catch (e) {
    console.error("Erreur récupération ID", e);
  }
};

const fetchCaisseVouchers = async () => {
  try {
    const res = await api.get('/caisse/');
    availableCaisseVouchers.value = res.data;
  } catch (e) {
    console.error("Erreur récupération pièces de caisse", e);
  }
};

const fetchHistory = async () => {
  try {
    const res = await api.get(`/bank-vouchers/?search=${searchQuery.value}`);
    history.value = res.data;
  } catch (e) {
    console.error("Erreur récupération historique", e);
  }
};

onMounted(() => {
  updatePeriod();
  fetchNextId();
  fetchCaisseVouchers();
  fetchHistory();
});

const addAllocation = () => {
  form.allocations.push({ cost_center_code: '', cost_center_name: '', client: '', analytical_account: '', amount: 0 });
};

const removeAllocation = (index) => {
  form.allocations.splice(index, 1);
};

const totalAllocation = computed(() => {
  return form.allocations.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);
});

const isTotalMatching = computed(() => {
  return Number(form.amount_in_numbers) > 0 && Math.abs(totalAllocation.value - Number(form.amount_in_numbers)) < 0.01;
});

const isFormValid = computed(() => {
  return form.allocations.length > 0 && isTotalMatching.value;
});

const submitVoucher = async () => {
  if (!isFormValid.value) return;
  try {
    const response = await api.post('/bank-vouchers/', form);
    
    if (response.data && response.data.pdf_url) {
      const url = response.data.pdf_url.startsWith('http') 
        ? response.data.pdf_url 
        : `${api.defaults.baseURL || 'http://localhost:8000'}/${response.data.pdf_url}`;
      window.open(url, '_blank');
    }
    
    // Open the attachment modal for the newly created voucher
    if (response.data && response.data.id) {
      selectedVoucherId.value = response.data.id;
      isAttachmentModalOpen.value = true;
    }
    
    // Reset form for next use
    form.bank_name = '';
    form.check_number = '';
    form.description = '';
    form.amount_in_numbers = 0;
    form.amount_in_letters = '';
    form.linked_caisse_voucher_ids = [];
    form.allocations = [
      { cost_center_code: '', cost_center_name: '', client: '', analytical_account: '', amount: 0 }
    ];
    
    // Fetch next ID for new voucher
    await fetchNextId();
    await fetchHistory();
  } catch (error) {
    console.error('Erreur :', error);
    if (error.response && error.response.data && error.response.data.detail) {
      alert(`Erreur : ${error.response.data.detail}`);
    } else {
      alert('Erreur lors de la communication avec le serveur.');
    }
  }
};
</script>

<style scoped>
.animate-pulse-once {
  animation: pulse-once 1s ease-in-out;
}
@keyframes pulse-once {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}
</style>
