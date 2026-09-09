<template>
  <AppLayout>
    <div class="w-full h-full flex flex-col gap-4 min-h-0">
      
      <!-- Top Header (shrinks to fit) -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shrink-0">
        <div>
          <h1 class="text-2xl sm:text-3xl font-black text-gray-900 flex items-center gap-3">
            <div class="p-2 bg-red-100 text-[#d10f2f] rounded-2xl flex items-center justify-center">
              <span class="material-symbols-outlined text-2xl">assignment</span>
            </div>
            <span>Gestion des demandes</span>
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            Consultez, filtrez et validez l'ensemble des demandes internes (RH, IT, Facilities et Carburant).
          </p>
        </div>

        <div class="flex items-center gap-3">
          <RouterLink
            to="/requests"
            class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-5 py-2.5 rounded-2xl shadow-lg shadow-red-200 transition flex items-center gap-2 font-semibold text-sm"
          >
            <span class="material-symbols-outlined text-lg">add_circle</span>
            <span>Nouvelle demande</span>
          </RouterLink>
        </div>
      </div>

      <!-- Categories & Scope Toolbar (shrinks to fit) -->
      <div class="bg-white rounded-3xl p-4 sm:p-5 shadow-[0_10px_30px_rgba(15,23,42,0.04)] border border-red-100 space-y-3 sm:space-y-4 shrink-0">
        
        <!-- Category Tabs -->
        <div class="flex flex-wrap items-center gap-1.5 sm:gap-2 border-b border-gray-100 pb-3 sm:pb-4">
          <button
            v-for="cat in categoryTabs"
            :key="cat.key"
            @click="activeCategory = cat.key"
            class="px-3 py-1.5 sm:px-4 sm:py-2 rounded-2xl text-xs font-bold transition flex items-center gap-1.5 sm:gap-2"
            :class="activeCategory === cat.key ? 'bg-red-600 text-white shadow-md shadow-red-200' : 'bg-gray-50 text-gray-600 hover:bg-red-50 hover:text-red-700'"
          >
            <span class="material-symbols-outlined text-base">{{ cat.icon }}</span>
            <span>{{ cat.label }}</span>
            <span 
              class="px-1.5 py-0.5 rounded-full text-[10px]"
              :class="activeCategory === cat.key ? 'bg-white/20 text-white' : 'bg-gray-200 text-gray-700'"
            >
              {{ getCategoryCount(cat.key) }}
            </span>
          </button>
        </div>

        <!-- Filters Row (Scope, Search, Status) -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          
          <!-- Scope Switch (Toutes / Mes demandes / Concerné) -->
          <div class="inline-flex rounded-2xl bg-gray-100 p-1">
            <button
              @click="activeScope = 'all'"
              class="px-3 py-1.5 rounded-xl text-xs font-bold transition"
              :class="activeScope === 'all' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'"
            >
              Toutes ({{ requests.length }})
            </button>
            <button
              @click="activeScope = 'mine'"
              class="px-3 py-1.5 rounded-xl text-xs font-bold transition"
              :class="activeScope === 'mine' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'"
            >
              Mes demandes ({{ myRequestsCount }})
            </button>
            <button
              @click="activeScope = 'concerning'"
              class="px-3 py-1.5 rounded-xl text-xs font-bold transition"
              :class="activeScope === 'concerning' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'"
            >
              À traiter ({{ concerningCount }})
            </button>
          </div>

          <!-- Search & Status Filters -->
          <div class="flex flex-wrap items-center gap-3">
            <div class="relative flex-1 sm:w-64">
              <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Rechercher réf, demandeur, objet..."
                class="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
              />
            </div>

            <select
              v-model="statusFilter"
              class="px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-xs font-medium text-gray-700 outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="ALL">Tous statuts</option>
              <option value="PENDING">En attente (PENDING)</option>
              <option value="PENDING_MANAGER_APPROVAL">Attente N+1 (Carburant)</option>
              <option value="PENDING_FINANCE_APPROVAL">Attente Finance (Carburant)</option>
              <option value="COMPROMISE_PENDING">Compromis proposé</option>
              <option value="APPROVED">Approuvé</option>
              <option value="REJECTED">Refusé</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Requests Table (grows to fill remaining space, scrolls internally) -->
      <div class="flex-1 min-h-0 flex flex-col bg-white rounded-3xl shadow-[0_15px_40px_rgba(127,7,28,0.06)] border border-red-100 overflow-hidden mb-4">
        <div class="flex-1 min-h-0 overflow-y-auto overflow-x-auto relative">
          
          <div v-if="loading" class="absolute inset-0 bg-white/70 backdrop-blur-[1px] flex items-center justify-center z-10">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
          </div>

          <table class="w-full text-left">
            <thead class="sticky top-0 z-20 shadow-xs">
              <tr class="bg-[#fcf3f4] text-left border-b border-red-100">
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c]">Réf / Date</th>
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c]">Catégorie</th>
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c]">Demandeur</th>
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c]">Détails & Objet</th>
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c]">Statut</th>
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c]">Document</th>
                <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-[#7f071c] text-right">Actions</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-red-100/50">
              <tr 
                v-for="req in filteredRequests" 
                :key="req.id" 
                class="hover:bg-red-50/50 transition-colors duration-150"
              >
                <!-- Réf & Date -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="font-bold text-gray-900 text-sm">{{ req.reference || 'DEM-' + String(req.id).padStart(4, '0') }}</div>
                  <div class="text-[11px] text-gray-400 mt-0.5">{{ formatDate(req.created_at) }}</div>
                </td>

                <!-- Catégorie badge -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span 
                    class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
                    :class="getCategoryBadgeClass(req)"
                  >
                    <span class="material-symbols-outlined text-sm">{{ getCategoryIcon(req) }}</span>
                    <span>{{ getCategoryLabel(req) }}</span>
                  </span>
                </td>

                <!-- Demandeur -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2.5">
                    <UserAvatar 
                      :name="req.requester_name" 
                      :photo-url="req.requester_photo_url"
                      size="sm" 
                    />
                    <div>
                      <div class="text-sm font-semibold text-gray-900">{{ req.requester_name || 'Utilisateur ' + req.requester_id }}</div>
                      <div v-if="req.requester_id === currentUser?.id" class="text-[10px] text-red-600 font-bold uppercase">Moi</div>
                    </div>
                  </div>
                </td>

                <!-- Détails selon le type -->
                <td class="px-6 py-4">
                  <!-- CARBURANT -->
                  <div v-if="req.type === 'FUEL'" class="space-y-1">
                    <div class="text-sm font-bold text-gray-900">
                      {{ req.payload?.trip_purpose || req.description || 'Déplacement' }}
                    </div>
                    <div class="flex flex-wrap items-center gap-2 text-xs text-gray-600">
                      <span class="inline-flex items-center gap-1 bg-amber-50 text-amber-800 px-2 py-0.5 rounded-md font-bold">
                        <span class="material-symbols-outlined text-[13px]">directions_car</span>
                        {{ req.payload?.vehicle_plate || 'Véhicule N/A' }}
                      </span>
                      <span class="inline-flex items-center gap-1 bg-gray-100 text-gray-700 px-2 py-0.5 rounded-md">
                        <span class="material-symbols-outlined text-[13px]">location_on</span>
                        {{ req.payload?.destination || 'Destination N/A' }}
                      </span>
                      <span class="font-extrabold text-red-700">
                        {{ req.payload?.fuel_quantity }} L
                        <span v-if="req.payload?.original_fuel_quantity" class="text-[10px] line-through text-gray-400 font-normal ml-1">
                          ({{ req.payload?.original_fuel_quantity }} L)
                        </span>
                      </span>
                    </div>
                  </div>

                  <!-- RH -->
                  <div v-else-if="req.type === 'LEAVE' || req.type === 'DOCUMENT'" class="space-y-1">
                    <div class="text-sm font-bold text-gray-900">
                      {{ req.payload?.reason || req.description || 'Demande RH' }}
                    </div>
                    <div v-if="req.type === 'LEAVE'" class="text-xs text-gray-500">
                      Du <span class="font-semibold text-gray-700">{{ req.payload?.start_date }}</span> au <span class="font-semibold text-gray-700">{{ req.payload?.end_date }}</span>
                      <span v-if="req.payload?.leave_type" class="ml-2 inline-block px-2 py-0.5 rounded bg-red-50 text-red-700 text-[11px] font-bold">
                        {{ req.payload?.leave_type }}
                      </span>
                    </div>
                  </div>

                  <!-- IT -->
                  <div v-else-if="req.type && req.type.startsWith('IT_')" class="space-y-1">
                    <div class="text-sm font-bold text-gray-900">
                      {{ req.payload?.affected_system || req.description || 'Ticket IT' }}
                    </div>
                    <div class="text-xs text-gray-500 line-clamp-1">
                      {{ req.payload?.error_message || req.description }}
                    </div>
                  </div>

                  <!-- FACILITIES -->
                  <div v-else class="space-y-1">
                    <div class="text-sm font-bold text-gray-900">
                      {{ req.description || req.payload?.description || req.payload?.justification || 'Demande Facilities' }}
                    </div>
                    <div class="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                      <span v-if="req.project_id || req.payload?.project_id" class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold text-[10px]">
                        Chantier #{{ req.project_id || req.payload?.project_id }}
                      </span>
                      <span v-if="req.payload?.location" class="px-2 py-0.5 rounded bg-gray-100 text-gray-600 text-[10px]">
                        {{ req.payload?.location }}
                      </span>
                      <span v-if="req.payload?.items && req.payload.items.length" class="text-xs text-gray-600 font-medium">
                        {{ req.payload.items.length }} article{{ req.payload.items.length > 1 ? 's' : '' }}
                      </span>
                    </div>
                  </div>
                </td>

                <!-- Statut -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusBadgeClass(req.status)" class="px-3 py-1 rounded-full text-xs font-bold uppercase">
                    {{ req.status }}
                  </span>
                </td>

                <!-- Document / PDF -->
                <td class="px-6 py-4 whitespace-nowrap text-xs">
                  <a 
                    v-if="req.type === 'FUEL'"
                    :href="getPdfUrl(req)" 
                    target="_blank" 
                    class="inline-flex items-center gap-1.5 font-bold text-[#d10f2f] hover:text-[#97091f] bg-red-50 hover:bg-red-100 px-3 py-1 rounded-xl transition shadow-xs"
                    title="Télécharger le bon DMCAR officiel"
                  >
                    <span class="material-symbols-outlined text-[16px]">picture_as_pdf</span>
                    <span>PDF DMCAR</span>
                  </a>
                  <a
                    v-else-if="req.attachment_url"
                    :href="req.attachment_url"
                    target="_blank"
                    class="inline-flex items-center gap-1 text-indigo-600 hover:underline font-medium"
                  >
                    <span class="material-symbols-outlined text-[16px]">attach_file</span>
                    Pièce jointe
                  </a>
                  <span v-else class="text-gray-400 italic text-[11px]">—</span>
                </td>

                <!-- Actions -->
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  
                  <!-- ACTIONS SPECIFIQUES CARBURANT -->
                  <div v-if="req.type === 'FUEL'" class="inline-flex items-center gap-1.5">
                    <template v-if="req.status === 'PENDING_MANAGER_APPROVAL'">
                      <button 
                        @click="updateStatus(req.id, 'PENDING_FINANCE_APPROVAL')"
                        class="text-blue-700 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                        title="Valider en tant que supérieur"
                      >
                        Valider N+1
                      </button>
                      <button 
                        @click="openRejectModal(req.id)"
                        class="text-red-700 bg-red-50 hover:bg-red-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Rejeter
                      </button>
                    </template>

                    <template v-else-if="req.status === 'PENDING_FINANCE_APPROVAL'">
                      <button 
                        @click="updateStatus(req.id, 'APPROVED')"
                        class="text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Valider
                      </button>
                      <button 
                        @click="openCompromiseModal(req)"
                        class="text-amber-700 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                        title="Modifier la quantité allouée"
                      >
                        Modifier Qté
                      </button>
                      <button 
                        @click="openRejectModal(req.id)"
                        class="text-red-700 bg-red-50 hover:bg-red-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Rejeter
                      </button>
                    </template>

                    <template v-else-if="req.status === 'COMPROMISE_PENDING'">
                      <button 
                        v-if="req.requester_id === currentUser?.id"
                        @click="updateStatus(req.id, 'APPROVED')"
                        class="text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Accepter Compromis
                      </button>
                      <button 
                        @click="openRejectModal(req.id)"
                        class="text-red-700 bg-red-50 hover:bg-red-100 px-2.5 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Rejeter
                      </button>
                    </template>

                    <button 
                      @click="deleteRequest(req.id)"
                      class="text-gray-400 hover:text-red-600 p-1 rounded-lg transition"
                      title="Supprimer la demande"
                    >
                      <span class="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </div>

                  <!-- ACTIONS STANDARDS (RH, IT, FACILITIES) -->
                  <div v-else class="inline-flex items-center gap-1.5">
                    <template v-if="req.status === 'PENDING'">
                      <button 
                        @click="updateStatus(req.id, 'APPROVED')"
                        class="text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-3 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Approuver
                      </button>
                      <button 
                        @click="openRejectModal(req.id)"
                        class="text-red-700 bg-red-50 hover:bg-red-100 px-3 py-1 rounded-lg text-xs font-bold transition"
                      >
                        Refuser
                      </button>
                    </template>
                    <span v-else class="text-gray-400 italic text-xs mr-2">Traitée</span>

                    <button 
                      v-if="req.requester_id === currentUser?.id || isUserAdmin"
                      @click="deleteRequest(req.id)"
                      class="text-gray-400 hover:text-red-600 p-1 rounded-lg transition"
                      title="Supprimer"
                    >
                      <span class="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </div>

                </td>
              </tr>

              <tr v-if="filteredRequests.length === 0 && !loading">
                <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                  <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-red-600 mb-3">
                    <span class="material-symbols-outlined text-2xl">search_off</span>
                  </div>
                  <p class="text-base font-semibold text-gray-900">Aucune demande trouvée</p>
                  <p class="text-xs text-gray-400 mt-1">Essayez de modifier vos filtres ou effectuez une nouvelle recherche.</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Reject Modal -->
      <div v-if="rejectModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-white p-6 rounded-3xl w-full max-w-md shadow-2xl space-y-4">
          <div class="flex items-center gap-3 text-red-600">
            <span class="material-symbols-outlined text-2xl">cancel</span>
            <h2 class="text-lg font-bold text-gray-900">Motif du refus</h2>
          </div>
          <p class="text-xs text-gray-500">Veuillez indiquer la raison pour laquelle cette demande est refusée :</p>
          <textarea 
            v-model="rejectionComment" 
            placeholder="Explication claire du refus..." 
            rows="3" 
            required 
            class="border border-gray-200 bg-gray-50 px-4 py-3 w-full rounded-2xl text-sm focus:outline-none focus:border-red-500 focus:bg-white transition"
          ></textarea>
          <div class="flex justify-end gap-3 pt-2">
            <button @click="rejectModalOpen = false" class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 text-sm font-semibold transition">Annuler</button>
            <button @click="confirmReject" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-5 py-2 rounded-xl text-sm font-semibold shadow-md transition">Confirmer le refus</button>
          </div>
        </div>
      </div>

      <!-- Fuel Compromise Modal (Modification de quantité) -->
      <div v-if="compromiseModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-white p-6 rounded-3xl w-full max-w-md shadow-2xl space-y-4">
          <div class="flex items-center gap-3 text-amber-600">
            <span class="material-symbols-outlined text-2xl">tune</span>
            <h2 class="text-lg font-bold text-gray-900">Ajuster la dotation en carburant</h2>
          </div>
          <p class="text-xs text-gray-500">
            Modifiez la quantité de carburant accordée. Le demandeur devra accepter ce compromis pour finaliser la validation.
          </p>
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Nouvelle quantité accordée (Litres)</label>
            <input 
              type="number" 
              step="0.1" 
              min="0.1" 
              v-model.number="compromiseQuantity" 
              class="border border-gray-200 bg-gray-50 px-4 py-3 w-full rounded-2xl text-sm focus:outline-none focus:border-red-500 focus:bg-white transition font-bold" 
            />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button @click="compromiseModalOpen = false" class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 text-sm font-semibold transition">Annuler</button>
            <button @click="confirmCompromise" class="bg-amber-600 hover:bg-amber-700 text-white px-5 py-2 rounded-xl text-sm font-semibold shadow-md transition">Valider le compromis</button>
          </div>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppLayout from '@/layouts/AppLayout.vue';
import UserAvatar from '@/components/common/UserAvatar.vue';
import api from '@/services/api';
import { useToast, useStatusBadges, useFormatters } from '@/composables';
import { getStoredProfile } from '@/services/session';

const route = useRoute();
const router = useRouter();
const toast = useToast();
const { getStatusBadgeClass } = useStatusBadges();
const { formatDate } = useFormatters();
const currentUser = getStoredProfile();

const isUserAdmin = computed(() => {
  return currentUser?.roles?.includes('Admin') || false;
});

const requests = ref<any[]>([]);
const loading = ref(false);

const activeCategory = ref<string>('ALL');
const activeScope = ref<'all' | 'mine' | 'concerning'>('all');
const searchQuery = ref<string>('');
const statusFilter = ref<string>('ALL');

const rejectModalOpen = ref(false);
const rejectionComment = ref('');
const currentRejectId = ref<number | null>(null);

const compromiseModalOpen = ref(false);
const selectedFuelReq = ref<any>(null);
const compromiseQuantity = ref<number>(0);

const categoryTabs = [
  { key: 'ALL', label: 'Toutes les demandes', icon: 'apps' },
  { key: 'HR', label: 'RH', icon: 'groups' },
  { key: 'IT', label: 'IT', icon: 'memory' },
  { key: 'FACILITIES_REPAIR', label: 'Facilities : Réparation & Bureau', icon: 'home_repair_service' },
  { key: 'FACILITIES_SITE', label: 'Facilities : Matériel Chantier', icon: 'construction' },
  { key: 'FUEL', label: 'Carburant (DMCAR)', icon: 'local_gas_station' },
];

const fetchRequests = async () => {
  loading.value = true;
  try {
    const res = await api.get('/requests/');
    requests.value = (res.data || []).sort((a: any, b: any) => b.id - a.id);
  } catch (error) {
    console.error("Error fetching requests", error);
    toast.error("Impossible de récupérer les demandes.");
  } finally {
    loading.value = false;
  }
};

const getCategory = (req: any): string => {
  if (req.type === 'FUEL') return 'FUEL';
  if (['LEAVE', 'DOCUMENT'].includes(req.type)) return 'HR';
  if (req.type && req.type.startsWith('IT_')) return 'IT';
  if (req.type === 'FACILITY_SUPPLIES' && !!req.project_id) return 'FACILITIES_SITE';
  if (req.type === 'FACILITY_MAINTENANCE' || req.type === 'FACILITY_SUPPLIES' || req.type === 'FACILITY_BADGE') {
    return 'FACILITIES_REPAIR';
  }
  return 'OTHER';
};

const getCategoryCount = (catKey: string): number => {
  if (catKey === 'ALL') return requests.value.length;
  return requests.value.filter(r => getCategory(r) === catKey).length;
};

const myRequestsCount = computed(() => {
  return requests.value.filter(req => req.requester_id === currentUser?.id).length;
});

const concerningCount = computed(() => {
  return requests.value.filter(req => req.requester_id !== currentUser?.id && ['PENDING', 'PENDING_MANAGER_APPROVAL', 'PENDING_FINANCE_APPROVAL'].includes(req.status)).length;
});

const getCategoryBadgeClass = (req: any): string => {
  const cat = getCategory(req);
  switch (cat) {
    case 'HR':
      return 'bg-purple-100 text-purple-800';
    case 'IT':
      return 'bg-blue-100 text-blue-800';
    case 'FACILITIES_REPAIR':
      return 'bg-teal-100 text-teal-800';
    case 'FACILITIES_SITE':
      return 'bg-amber-100 text-amber-900';
    case 'FUEL':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getCategoryIcon = (req: any): string => {
  const cat = getCategory(req);
  switch (cat) {
    case 'HR': return 'groups';
    case 'IT': return 'memory';
    case 'FACILITIES_REPAIR': return 'home_repair_service';
    case 'FACILITIES_SITE': return 'construction';
    case 'FUEL': return 'local_gas_station';
    default: return 'help';
  }
};

const getCategoryLabel = (req: any): string => {
  const cat = getCategory(req);
  switch (cat) {
    case 'HR': return 'RH';
    case 'IT': return 'IT';
    case 'FACILITIES_REPAIR': return 'Réparation / Bureau';
    case 'FACILITIES_SITE': return 'Matériel Chantier';
    case 'FUEL': return 'Carburant';
    default: return req.type || 'Autre';
  }
};

const getPdfUrl = (req: any) => {
  const baseUrl = api.defaults.baseURL || `http://${window.location.hostname}:8000`;
  return `${baseUrl}/requests/${req.id}/download-pdf`;
};

const filteredRequests = computed(() => {
  return requests.value.filter((req) => {
    // 1. Category tab
    if (activeCategory.value !== 'ALL') {
      if (getCategory(req) !== activeCategory.value) return false;
    }

    // 2. Scope
    if (activeScope.value === 'mine') {
      if (req.requester_id !== currentUser?.id) return false;
    } else if (activeScope.value === 'concerning') {
      if (req.requester_id === currentUser?.id) return false;
    }

    // 3. Status
    if (statusFilter.value !== 'ALL') {
      if (req.status !== statusFilter.value) return false;
    }

    // 4. Search query
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase().trim();
      const ref = (req.reference || `dem-${req.id}`).toLowerCase();
      const requester = (req.requester_name || '').toLowerCase();
      const desc = (req.description || '').toLowerCase();
      const plate = (req.payload?.vehicle_plate || '').toLowerCase();
      const dest = (req.payload?.destination || '').toLowerCase();
      const purpose = (req.payload?.trip_purpose || '').toLowerCase();
      const reason = (req.payload?.reason || '').toLowerCase();

      const match = ref.includes(q) || requester.includes(q) || desc.includes(q) ||
        plate.includes(q) || dest.includes(q) || purpose.includes(q) || reason.includes(q);

      if (!match) return false;
    }

    return true;
  });
});

const updateStatus = async (id: number, status: string, comment: string | null = null, updatedPayload: any = null) => {
  try {
    const payload: any = {
      status: status,
      rejection_comment: comment
    };
    if (updatedPayload) {
      payload.updated_payload = updatedPayload;
    }
    await api.patch(`/requests/${id}/status`, payload);
    toast.success("Statut mis à jour avec succès.");
    await fetchRequests();
  } catch (error) {
    console.error("Error updating status", error);
    toast.error("Erreur lors de la mise à jour du statut.");
  }
};

const openRejectModal = (id: number) => {
  currentRejectId.value = id;
  rejectionComment.value = '';
  rejectModalOpen.value = true;
};

const confirmReject = async () => {
  if (currentRejectId.value) {
    await updateStatus(currentRejectId.value, 'REJECTED', rejectionComment.value);
    rejectModalOpen.value = false;
  }
};

const openCompromiseModal = (req: any) => {
  selectedFuelReq.value = req;
  compromiseQuantity.value = req.payload?.fuel_quantity || 1;
  compromiseModalOpen.value = true;
};

const confirmCompromise = async () => {
  if (!selectedFuelReq.value) return;
  const newQty = parseFloat(String(compromiseQuantity.value));
  if (isNaN(newQty) || newQty <= 0) {
    toast.error("Quantité invalide.");
    return;
  }

  const updated = {
    ...selectedFuelReq.value.payload,
    fuel_quantity: newQty
  };

  await updateStatus(selectedFuelReq.value.id, 'COMPROMISE_PENDING', null, updated);
  compromiseModalOpen.value = false;
};

const deleteRequest = async (id: number) => {
  if (!confirm("Voulez-vous vraiment supprimer cette demande ?")) return;
  try {
    await api.delete(`/requests/${id}`);
    toast.success("Demande supprimée.");
    await fetchRequests();
  } catch (error) {
    console.error("Error deleting request", error);
    toast.error("Erreur lors de la suppression de la demande.");
  }
};

onMounted(() => {
  // If navigated with ?category=fuel (from old fuel-requests redirect)
  if (route.query.category === 'fuel') {
    activeCategory.value = 'FUEL';
  }
  fetchRequests();
});

watch(() => route.query.category, (newCat) => {
  if (newCat === 'fuel') {
    activeCategory.value = 'FUEL';
  }
});
</script>
