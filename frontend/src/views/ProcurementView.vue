<script setup lang="ts">
import { ref, onMounted } from 'vue';
import AppLayout from "@/layouts/AppLayout.vue";
import api from "@/services/api";
import { StockService } from "@/services/stock";
import { useToast, useFormatters, useTableSort, useDebounceFn, useStatusBadges } from "@/composables";
import { getStoredProfile } from "@/services/session";

const toast = useToast();
const { formatMonthDay, formatYear, formatCurrency } = useFormatters();
const { getStatusBadgeClass } = useStatusBadges();

const purchaseRequests = ref<any[]>([]);
const purchaseOrders = ref<any[]>([]);
const projects = ref<any[]>([]);
const partners = ref<any[]>([]);
const products = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const showRequestModal = ref(false);
const showOrderModal = ref(false);
const isSubmitting = ref(false);

const searchQuery = ref('');

const { sortColumn, sortOrder, sortBy, sortedItems: sortedOrders } = useTableSort(purchaseOrders, 'id', 'desc');

const requestForm = ref({
  project_id: '',
  description: '',
  expected_date: ''
});

const orderForm = ref({
  purchase_request_id: '',
  supplier_id: '',
  lines: [] as Array<{ product_id: string, quantity: number, unit_price: number }>
});

const showApproveModal = ref(false);
const orderToApprove = ref<any>(null);
const approveLines = ref<any[]>([]);
const availableBudgets = ref<any[]>([]);

const addLine = () => {
  orderForm.value.lines.push({ product_id: '', quantity: 1, unit_price: 0 });
};

const removeLine = (index: number) => {
  orderForm.value.lines.splice(index, 1);
};

const fetchData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const searchParam = searchQuery.value ? `?search=${encodeURIComponent(searchQuery.value)}` : '';
    const [requestsRes, ordersRes, projRes, partRes, prodRes] = await Promise.all([
      api.get('/procurement/requests/'),
      api.get(`/procurement/orders/${searchParam}`),
      api.get('/projects/'),
      StockService.getPartners(),
      StockService.getProducts()
    ]);
    
    purchaseRequests.value = requestsRes.data;
    purchaseOrders.value = ordersRes.data;
    projects.value = projRes.data;
    partners.value = partRes.data;
    products.value = prodRes.data;
  } catch (err: any) {
    console.error("Failed to fetch procurement data", err);
    error.value = "Erreur lors du chargement des données d'achat.";
  } finally {
    loading.value = false;
  }
};

const { debounced: debouncedSearch } = useDebounceFn(fetchData, 300);

const createPurchaseRequest = async () => {
  if (!requestForm.value.project_id) {
    toast.error("Veuillez sélectionner un projet.");
    return;
  }

  isSubmitting.value = true;
  try {
    await api.post('/procurement/requests/', {
      project_id: Number(requestForm.value.project_id),
      description: requestForm.value.description || undefined,
      expected_date: requestForm.value.expected_date || undefined,
      requester_id: null
    });
    
    toast.success("Demande d'achat créée avec succès !");
    showRequestModal.value = false;
    requestForm.value = { project_id: '', description: '', expected_date: '' };
    await fetchData();
  } catch (err: any) {
    toast.error("Erreur lors de la création de la demande d'achat.");
  } finally {
    isSubmitting.value = false;
  }
};

const createPurchaseOrder = async () => {
  isSubmitting.value = true;
  try {
    await api.post('/procurement/orders/', {
      purchase_request_id: orderForm.value.purchase_request_id ? Number(orderForm.value.purchase_request_id) : null,
      supplier_id: orderForm.value.supplier_id ? Number(orderForm.value.supplier_id) : null,
      lines: orderForm.value.lines.map(line => ({
        product_id: Number(line.product_id),
        quantity: Number(line.quantity),
        unit_price: Number(line.unit_price)
      }))
    });
    
    toast.success("Bon de commande créé avec succès !");
    showOrderModal.value = false;
    orderForm.value = { purchase_request_id: '', supplier_id: '', lines: [] };
    await fetchData();
  } catch (err: any) {
    toast.error("Erreur lors de la création du bon de commande.");
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  fetchData();
});

const openApproveModal = async (order: any) => {
  orderToApprove.value = order;
  approveLines.value = (order.lines || []).map((l: any) => ({
    line_id: l.id,
    budget_id: '',
    designation: l.designation,
    quantity: l.quantity,
    unit_price: l.unit_price,
    product_id: l.product_id
  }));
  
  let projId = order.project_id;
  if (!projId && order.purchase_request_id) {
     const req = purchaseRequests.value.find(r => r.id === order.purchase_request_id);
     if (req) projId = req.project_id;
  }
  
  if (projId) {
    try {
      const res = await api.get(`/projects/${projId}/budgets`);
      availableBudgets.value = res.data;
    } catch (e) {
      console.error("Failed to load budgets");
      availableBudgets.value = [];
    }
  } else {
    availableBudgets.value = [];
  }
  
  showApproveModal.value = true;
};

const submitApproval = async () => {
  isSubmitting.value = true;
  try {
    const payload = {
      lines: approveLines.value.map(l => ({
        line_id: l.line_id,
        budget_id: l.budget_id ? Number(l.budget_id) : null
      }))
    };
    await api.put(`/procurement/orders/${orderToApprove.value.id}/approve`, payload);
    toast.success("Bon de commande approuvé !");
    showApproveModal.value = false;
    await fetchData();
  } catch (err: any) {
    toast.error(err.response?.data?.detail || "Erreur lors de l'approbation.");
  } finally {
    isSubmitting.value = false;
  }
};

const downloadOrderPdf = async (orderId: number) => {
  try {
    toast.success("Génération du PDF en cours...");
    const res = await api.get(`/procurement/orders/${orderId}/download-pdf/`);
    if (res.data && res.data.pdf_url) {
      window.open(res.data.pdf_url, '_blank');
    }
  } catch (err: any) {
    toast.error("Erreur lors de la génération du PDF du Bon de Commande.");
  }
};
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-8 w-full">
      
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Module Achats</h1>
          <p class="mt-1 text-gray-500">Gestion des demandes d'achat et bons de commande</p>
        </div>
        <div class="flex gap-4">
          <button @click="showOrderModal = true" class="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors">
            Créer un Bon de Commande
          </button>
          <button @click="showRequestModal = true" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
            <span class="material-symbols-outlined text-sm">add</span>
            Nouvelle Demande
          </button>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-[300px] relative">
        <div v-if="loading && (!purchaseOrders.length && !purchaseRequests.length)" class="absolute inset-0 bg-white/80 z-20 flex justify-center items-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
        </div>


      <div v-else-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg">
        {{ error }}
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Purchase Requests -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="p-6 border-b border-gray-100">
            <h2 class="text-xl font-bold text-gray-900">Demandes d'Achats</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                <tr>
                  <th class="px-6 py-4 font-medium">Projet</th>
                  <th class="px-6 py-4 font-medium">Description</th>
                  <th class="px-6 py-4 font-medium">Date Prévue</th>
                  <th class="px-6 py-4 font-medium">Année</th>
                  <th class="px-6 py-4 font-medium">Statut</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="req in purchaseRequests" :key="req.id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-6 py-4 text-sm font-medium text-gray-900">#{{ req.project_id }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ req.description || '-' }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ req.expected_date ? new Date(req.expected_date).toLocaleDateString('fr-FR', { month: '2-digit', day: '2-digit' }) : '-' }}</td>
                  <td class="px-6 py-4 text-sm font-bold text-gray-700">{{ req.expected_date ? new Date(req.expected_date).getFullYear() : '-' }}</td>
                  <td class="px-6 py-4">
                    <span :class="{'bg-green-100 text-green-800': req.status === 'Approved', 'bg-yellow-100 text-yellow-800': req.status === 'Pending'}" class="px-2 py-1 text-xs font-semibold rounded-full">
                      {{ req.status }}
                    </span>
                  </td>
                </tr>
                <tr v-if="purchaseRequests.length === 0">
                  <td colspan="4" class="px-6 py-8 text-center text-gray-500">Aucune demande d'achat.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Purchase Orders -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
          <div class="p-4 border-b border-gray-100 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">Bons de Commande</h2>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
              <input 
                v-model="searchQuery" 
                @input="debouncedSearch"
                class="pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 transition-shadow w-48" 
                placeholder="Rechercher BC..."
              >
            </div>
          </div>
          <div class="overflow-x-auto flex-1 relative min-h-[200px]">
            <div v-if="loading" class="absolute inset-0 bg-white/50 flex justify-center items-center z-10 backdrop-blur-[1px]">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
            </div>
            <table class="w-full text-left">
              <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                <tr>
                  <th @click="sortBy('id')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                    <div class="flex items-center gap-1">ID BC <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'id'}">{{ sortColumn === 'id' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                  </th>
                  <th @click="sortBy('purchase_request_id')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                    <div class="flex items-center gap-1">Demande <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'purchase_request_id'}">{{ sortColumn === 'purchase_request_id' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                  </th>
                  <th @click="sortBy('total_amount')" class="px-6 py-4 font-medium cursor-pointer hover:bg-gray-100 transition-colors group">
                    <div class="flex items-center gap-1">Montant <span class="material-symbols-outlined text-[16px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'total_amount'}">{{ sortColumn === 'total_amount' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
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
                  <th class="px-6 py-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="order in sortedOrders" :key="order.id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-6 py-4 text-sm font-bold text-gray-900">BC-{{ order.id }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">DA-{{ order.purchase_request_id || '-' }}</td>
                  <td class="px-6 py-4 text-sm font-bold text-gray-900">{{ order.total_amount }} XOF</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ formatMonthDay(order.created_at) }}</td>
                  <td class="px-6 py-4 text-sm font-bold text-gray-700">{{ formatYear(order.created_at) }}</td>
                  <td class="px-6 py-4">
                    <span :class="getStatusBadgeClass(order.status)" class="px-2.5 py-1 text-xs font-semibold rounded-full">
                      {{ order.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                      <button v-if="order.status !== 'Approved' && order.status !== 'Cancelled'" @click="openApproveModal(order)" class="text-green-600 hover:text-green-900 font-medium flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">check_circle</span>
                        Approuver
                      </button>
                      <button @click="downloadOrderPdf(order.id)" class="text-indigo-600 hover:text-indigo-900 font-medium flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">download</span>
                        PDF
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="sortedOrders.length === 0">
                  <td colspan="7" class="px-6 py-8 text-center text-gray-500">Aucun bon de commande.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      </div>
      
    </div>

    <!-- Modal Nouvelle Demande d'Achat -->
    <div v-if="showRequestModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-full max-w-md shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Nouvelle Demande d'Achat</h2>
        <form @submit.prevent="createPurchaseRequest" class="space-y-4">
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Projet</label>
            <select v-model="requestForm.project_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500">
              <option value="" disabled>Sélectionner un projet</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.code }} - {{ p.nom }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Date Prévue</label>
            <input type="date" v-model="requestForm.expected_date" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="requestForm.description" rows="3" placeholder="Description de l'achat" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500"></textarea>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <button type="button" @click="showRequestModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors">
              Annuler
            </button>
            <button type="submit" :disabled="isSubmitting" class="px-4 py-2 bg-[#d10f2f] hover:bg-[#97091f] text-white rounded-lg font-medium transition-colors disabled:opacity-70 flex items-center justify-center min-w-[120px]">
              <div v-if="isSubmitting" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
              <span v-else>Créer</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Nouveau Bon de Commande -->
    <div v-if="showOrderModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-full max-w-md shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Créer un Bon de Commande</h2>
        <form @submit.prevent="createPurchaseOrder" class="space-y-4">
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Demande d'Achat Liée</label>
            <select v-model="orderForm.purchase_request_id" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500">
              <option value="">Aucune (Direct)</option>
              <option v-for="req in purchaseRequests" :key="req.id" :value="req.id">{{ req.reference || 'DEM-' + req.id }} (Projet #{{ req.project_id }})</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fournisseur</label>
            <select v-model="orderForm.supplier_id" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500">
              <option value="">Sélectionner un fournisseur</option>
              <option v-for="part in partners" :key="part.id" :value="part.id">{{ part.name }}</option>
            </select>
          </div>

          <div class="border-t border-gray-200 pt-4 mt-4">
            <div class="flex justify-between items-center mb-2">
              <label class="block text-sm font-medium text-gray-700">Lignes de Commande</label>
              <button type="button" @click="addLine" class="text-xs text-red-600 hover:text-red-800 font-medium">+ Ajouter une Ligne</button>
            </div>
            
            <div class="space-y-3 max-h-[300px] overflow-y-auto pr-2">
              <div v-for="(line, idx) in orderForm.lines" :key="idx" class="flex gap-2 items-start bg-gray-50 p-2 rounded-lg border border-gray-100">
                <div class="flex-1">
                  <select v-model="line.product_id" required class="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:border-red-500">
                    <option value="">Produit</option>
                    <option v-for="prod in products" :key="prod.id" :value="prod.id">{{ prod.designation }}</option>
                  </select>
                </div>
                <div class="w-20">
                  <input type="number" v-model="line.quantity" min="1" required placeholder="Qté" class="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:border-red-500" />
                </div>
                <div class="w-24">
                  <input type="number" v-model="line.unit_price" min="0" step="0.01" required placeholder="Prix U." class="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:border-red-500" />
                </div>
                <button type="button" @click="removeLine(idx)" class="text-gray-400 hover:text-red-500 mt-1">
                  <span class="material-symbols-outlined text-sm">close</span>
                </button>
              </div>
              <div v-if="orderForm.lines.length === 0" class="text-xs text-gray-500 text-center py-4 italic">
                Aucun article ajouté.
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <button type="button" @click="showOrderModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors">
              Annuler
            </button>
            <button type="submit" :disabled="isSubmitting" class="px-4 py-2 bg-[#d10f2f] hover:bg-[#97091f] text-white rounded-lg font-medium transition-colors disabled:opacity-70 flex items-center justify-center min-w-[120px]">
              <div v-if="isSubmitting" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
              <span v-else>Créer</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Approbation & Imputation Budgétaire -->
    <div v-if="showApproveModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-full max-w-2xl shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Approuver & Imputer (BC-{{ orderToApprove?.id }})</h2>
        <form @submit.prevent="submitApproval" class="space-y-4">
          
          <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 class="text-sm font-bold text-gray-700 mb-2">Lignes de la commande</h3>
            <div class="space-y-3 max-h-[300px] overflow-y-auto">
              <div v-for="(line, idx) in approveLines" :key="idx" class="flex gap-4 items-center bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900">
                    {{ line.designation || (products.find(p => p.id === line.product_id)?.designation) || 'Produit inconnu' }}
                  </p>
                  <p class="text-xs text-gray-500">Qté: {{ line.quantity }} | Prix: {{ line.unit_price }}</p>
                </div>
                <div class="w-1/2">
                  <select v-model="line.budget_id" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-500">
                    <option value="">-- Sans budget --</option>
                    <option v-for="b in availableBudgets" :key="b.id" :value="b.id">
                      {{ b.category }} (Reste: {{ b.allocated_amount - b.consumed }} {{ b.currency }})
                    </option>
                  </select>
                </div>
              </div>
              <div v-if="approveLines.length === 0" class="text-sm text-gray-500 text-center py-4">
                Aucune ligne trouvée sur ce BC.
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <button type="button" @click="showApproveModal = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors">
              Annuler
            </button>
            <button type="submit" :disabled="isSubmitting" class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-70 flex items-center justify-center min-w-[120px]">
              <div v-if="isSubmitting" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
              <span v-else>Approuver</span>
            </button>
          </div>
        </form>
      </div>
    </div>

  </AppLayout>
</template>
