<template>
  <AppLayout>
    <div class="w-full flex flex-col">
        <div class="flex justify-between items-center mb-6">
          <h1 class="text-2xl font-bold mb-4 text-[#b30c27] flex items-center gap-2">
            <span class="material-symbols-outlined">local_gas_station</span>
            <span>Demandes de Carburant (DMCAR)</span>
          </h1>
          <button 
            @click="showCreateModal = true"
            class="bg-[#d10f2f] text-white px-4 py-2 rounded-xl hover:bg-[#97091f] shadow-[0_10px_30px_rgba(209,15,47,0.28)] transition flex items-center gap-2 mb-6"
          >
            <span class="material-symbols-outlined">add</span>
            <span>Nouvelle Demande</span>
          </button>
        </div>

        <!-- Tableau des demandes -->
        <div class="bg-white rounded-2xl shadow-[0_15px_40px_rgba(127,7,28,0.10)] border border-red-100 overflow-hidden">
          <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
            <h2 class="text-xl font-bold text-gray-900">Demandes de Carburant</h2>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
              <input 
                v-model="searchQuery" 
                @input="debouncedSearch"
                class="pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 transition-shadow w-64" 
                placeholder="Rechercher une demande..."
              >
            </div>
          </div>
          <div class="overflow-x-auto relative min-h-[200px]">
            <div v-if="loading" class="absolute inset-0 bg-white/50 flex justify-center items-center z-10 backdrop-blur-[1px]">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
            </div>
            <table class="w-full">
            <thead>
              <tr class="bg-gradient-to-r from-red-100/90 to-red-50 text-left">
                <th @click="sortBy('id')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition group">
                  <div class="flex items-center gap-2">ID <span class="material-symbols-outlined text-sm text-red-300 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'id'}">{{ sortColumn === 'id' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('request_date')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition group">
                  <div class="flex items-center gap-2">Date <span class="material-symbols-outlined text-sm text-red-300 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'request_date'}">{{ sortColumn === 'request_date' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('request_date')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition group">
                  <div class="flex items-center gap-2">Année <span class="material-symbols-outlined text-sm text-red-300 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'request_date'}">{{ sortColumn === 'request_date' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('employee_name')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition group">
                  <div class="flex items-center gap-2">Employé / Véhicule <span class="material-symbols-outlined text-sm text-red-300 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'employee_name'}">{{ sortColumn === 'employee_name' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('fuel_quantity')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition group">
                  <div class="flex items-center gap-2">Quantité <span class="material-symbols-outlined text-sm text-red-300 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'fuel_quantity'}">{{ sortColumn === 'fuel_quantity' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th @click="sortBy('status')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition group">
                  <div class="flex items-center gap-2">Statut <span class="material-symbols-outlined text-sm text-red-300 opacity-0 group-hover:opacity-100 transition-opacity" :class="{'opacity-100 text-red-500': sortColumn === 'status'}">{{ sortColumn === 'status' && sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}</span></div>
                </th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">PDF</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="req in sortedRequests" :key="req.id" class="border-t border-red-100/80 hover:bg-red-50/70 transition">
                <td class="px-6 py-4 text-sm font-bold text-gray-900">{{ req.reference || 'DEM-' + req.id }}</td>
                <td class="px-6 py-4 text-gray-600 font-medium whitespace-nowrap">{{ new Date(req.request_date).toLocaleDateString('fr-FR', { month: '2-digit', day: '2-digit' }) }}</td>
                <td class="px-6 py-4 text-sm font-bold text-gray-700">{{ new Date(req.request_date).getFullYear() }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ req.employee_name || 'N/A' }}</div>
                  <div class="text-xs text-gray-500">{{ req.vehicule_matricule }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-gray-700">
                  <span class="font-bold">{{ req.fuel_quantity }} L</span>
                  <span v-if="req.original_fuel_quantity" class="ml-2 text-xs text-red-500 line-through">({{ req.original_fuel_quantity }} L)</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-3 py-1 rounded-full text-xs font-medium uppercase bg-amber-100 text-amber-700">
                    {{ req.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <a v-if="req.pdf_url" :href="getPdfUrl(req)" target="_blank" class="text-indigo-600 hover:text-indigo-900 flex items-center gap-1 font-semibold">
                    <span class="material-symbols-outlined text-lg">picture_as_pdf</span>
                    Télécharger PDF
                  </a>
                  <span v-else class="text-gray-400 italic">Non généré</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div v-if="req.status === 'PENDING_MANAGER_APPROVAL'" class="flex gap-2">
                    <button 
                      @click="validateManager(req.id)"
                      class="text-blue-600 hover:text-blue-900"
                    >
                      Valider Supérieur
                    </button>
                    <button 
                      @click="rejectRequest(req.id)"
                      class="text-red-600 hover:text-red-900"
                    >
                      Rejeter
                    </button>
                  </div>
                  <div v-else-if="req.status === 'PENDING_FINANCE_APPROVAL'" class="flex gap-2">
                    <button 
                      @click="validateFinance(req.id)"
                      class="text-emerald-600 hover:text-emerald-900"
                    >
                      Valider
                    </button>
                    <button 
                      @click="compromiseFinance(req.id)"
                      class="text-amber-600 hover:text-amber-900"
                    >
                      Modifier Qté
                    </button>
                    <button 
                      @click="rejectRequest(req.id)"
                      class="text-red-600 hover:text-red-900"
                    >
                      Rejeter
                    </button>
                  </div>
                  <div v-else-if="req.status === 'COMPROMISE_PENDING'" class="flex gap-2">
                    <button 
                      @click="acceptCompromise(req.id)"
                      class="text-emerald-600 hover:text-emerald-900"
                    >
                      Accepter Compromis
                    </button>
                    <button 
                      @click="rejectRequest(req.id)"
                      class="text-red-600 hover:text-red-900"
                    >
                      Rejeter
                    </button>
                  </div>
                  <button 
                    @click="deleteRequest(req.id)"
                    class="ml-3 text-red-600 hover:text-red-900"
                    title="Supprimer la demande"
                  >
                    <span class="material-symbols-outlined text-lg align-middle">delete</span>
                  </button>
                </td>
              </tr>
              <tr v-if="sortedRequests.length === 0">
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">Aucune demande trouvée.</td>
              </tr>
            </tbody>
          </table>
          </div>
        </div>


    <!-- Modal Nouvelle Demande -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
        <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
          <h2 class="text-xl font-bold flex items-center gap-2">
            <span class="material-symbols-outlined">description</span>
            Nouvelle Demande de Carburant
          </h2>
          <button @click="showCreateModal = false" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <form @submit.prevent="submitRequest" class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input 
                type="date" 
                v-model="form.request_date" 
                required
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">N° Affaire (Optionnel)</label>
              <input type="text" v-model="form.affaire_no" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">N° Dossier (Optionnel)</label>
              <input type="text" v-model="form.dossier_no" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Objet du Déplacement</label>
              <input type="text" v-model="form.objet_deplacement" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Matricule Véhicule</label>
              <input type="text" v-model="form.vehicule_matricule" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Destination</label>
              <input type="text" v-model="form.destination" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Relevé Kilométrique</label>
              <input type="number" v-model="form.releve_kilometrique" required min="1" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre de jours</label>
              <input type="number" v-model="form.nombre_jours" required min="1" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Quantité de carburant (Litres)</label>
              <input type="number" step="0.01" v-model="form.quantite_carburant" required min="0.01" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
          </div>
          <div class="mt-8 flex justify-end gap-3 pt-4 border-t">
            <button type="button" @click="showCreateModal = false" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">
              Annuler
            </button>
            <button type="submit" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition">
              Créer la demande
            </button>
          </div>
        </form>
      </div>
    </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import { api } from '@/services/api';
import { employeeService } from '@/services/employees';
import { useToast } from '@/composables/useToast';

const toast = useToast();

const requests = ref<any[]>([]);
const showCreateModal = ref(false);
const loading = ref(false);

const searchQuery = ref('');
let debounceTimer: any = null;

const sortColumn = ref('id');
const sortOrder = ref<'asc' | 'desc'>('desc');

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortOrder.value = 'asc';
  }
};

const debouncedSearch = () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchRequests();
  }, 300);
};

const sortedRequests = computed(() => {
  return [...requests.value].sort((a, b) => {
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

const getPdfUrl = (req: any) => {
  const baseUrl = api.defaults.baseURL || `http://${window.location.hostname}:8000`;
  return `${baseUrl}/requests/${req.id}/download-pdf`;
};

const form = ref({
  request_date: new Date().toISOString().split('T')[0],
  affaire_no: '',
  dossier_no: '',
  vehicule_matricule: '',
  objet_deplacement: '',
  destination: '',
  releve_kilometrique: 0,
  nombre_jours: 1,
  quantite_carburant: 0,
});

async function fetchRequests() {
  loading.value = true;
  try {
    const searchParam = searchQuery.value ? `&search=${encodeURIComponent(searchQuery.value)}` : '';
    const res = await api.get(`/requests/?type=FUEL${searchParam}`);
    requests.value = res.data.map((req: any) => ({
      ...req.payload,
      id: req.id,
      status: req.status,
      request_date: req.created_at,
      pdf_url: req.attachment_url,
      employee_name: req.requester_name || 'N/A'
    }));
  } catch (e) {
    console.error("Error fetching requests", e);
  } finally {
    loading.value = false;
  }
}


async function submitRequest() {
  try {
    await api.post('/requests/', {
      type: 'FUEL',
      project_id: parseInt(form.value.project_id) || null,
      description: form.value.objet_deplacement || "Demande de carburant",
      payload: { 
        type: 'FUEL',
        request_date: form.value.request_date,
        vehicle_plate: form.value.vehicule_matricule,
        destination: form.value.destination,
        fuel_quantity: parseFloat(form.value.quantite_carburant) || 1,
        trip_days: 1, 
        odometer_reading: parseInt(form.value.releve_kilometrique) || 1,
        trip_purpose: form.value.objet_deplacement,
        affaire_no: form.value.affaire_no,
        dossier_no: form.value.dossier_no
      }
    });
    showCreateModal.value = false;
    form.value.affaire_no = '';
    form.value.dossier_no = '';
    form.value.vehicule_matricule = '';
    form.value.objet_deplacement = '';
    form.value.destination = '';
    form.value.releve_kilometrique = 0;
    form.value.quantite_carburant = 0;
    
    await fetchRequests();
  } catch (e) {
    console.error("Error creating request", e);
    toast.error("Erreur lors de la création de la demande");
  }
}

async function validateManager(id: number) {
  try {
    await api.patch(`/requests/${id}/status`, {
      status: 'PENDING_FINANCE_APPROVAL'
    });
    await fetchRequests();
    toast.success("Demande validée par le supérieur !");
  } catch (e) {
    console.error("Error validating manager", e);
    toast.error("Erreur lors de la validation. Êtes-vous le supérieur direct ou un membre de la direction ?");
  }
}

async function validateFinance(id: number) {
  try {
    await api.patch(`/requests/${id}/status`, {
      status: 'APPROVED'
    });
    await fetchRequests();
    toast.success("Demande validée par la finance ! Le PDF a été généré dans MinIO.");
  } catch (e) {
    console.error("Error validating finance", e);
    toast.error("Erreur lors de la validation. Vérifiez vos permissions.");
  }
}

async function compromiseFinance(id: number) {
  const amount = prompt("Nouvelle quantité de carburant accordée (en Litres) :");
  if (amount === null || amount.trim() === '') return;
  
  const parsed = parseFloat(amount);
  if (isNaN(parsed) || parsed <= 0) {
    toast.error("Quantité invalide");
    return;
  }
  
  try {
    await api.patch(`/requests/${id}/status`, {
      status: 'APPROVED',
      updated_payload: {
        fuel_quantity: parsed
      }
    });
    await fetchRequests();
    toast.success("Compromis proposé ! En attente du supérieur direct.");
  } catch (e) {
    console.error("Error proposing compromise", e);
    toast.error("Erreur lors de la proposition du compromis.");
  }
}

async function acceptCompromise(id: number) {
  try {
    await api.patch(`/requests/${id}/status`, {
      status: 'APPROVED'
    });
    await fetchRequests();
    toast.success("Compromis accepté ! La demande est validée.");
  } catch (e) {
    console.error("Error accepting compromise", e);
    toast.error("Erreur lors de l'acceptation du compromis.");
  }
}

async function rejectRequest(id: number) {
  const reason = prompt("Raison du rejet :");
  if (reason === null) return;
  try {
    await api.patch(`/requests/${id}/status`, {
      status: 'REJECTED',
      rejection_comment: reason
    });
    await fetchRequests();
    toast.success("Demande rejetée.");
  } catch (e) {
    console.error("Error rejecting", e);
    toast.error("Erreur lors du rejet.");
  }
}

async function deleteRequest(id: number) {
  if (!confirm("Voulez-vous vraiment supprimer cette demande ?")) return;
  try {
    await api.delete(`/requests/${id}`);
    await fetchRequests();
  } catch (e) {
    console.error("Error deleting request", e);
    toast.error("Erreur lors de la suppression. Vérifiez vos permissions.");
  }
}

onMounted(async () => {
  fetchRequests();
});
</script>
