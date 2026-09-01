<template>
  <AppLayout>
    <div class="w-full flex flex-col">
        <div class="flex justify-between items-center mb-6">
          <h1 class="text-2xl font-bold mb-4 text-[#b30c27] flex items-center gap-2">
            <span class="material-symbols-outlined">assignment</span>
            <span>Mes demandes</span>
          </h1>
        </div>

        <h2 class="text-xl font-bold mb-4 mt-4 text-gray-800">Toutes mes demandes et leurs états</h2>
        <div class="bg-white rounded-2xl shadow-[0_15px_40px_rgba(127,7,28,0.10)] border border-red-100 overflow-x-auto mb-8">
          <table class="min-w-max w-full">
            <thead>
              <tr class="bg-gradient-to-r from-red-100/90 to-red-50 text-left">
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">ID</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Type</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Détails / Raison</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Date de création</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Statut</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="req in myRequests" :key="req.id" class="border-t border-red-100/80 hover:bg-red-50/70 transition">
                <td class="px-6 py-4 text-gray-600 font-medium">{{ req.reference || 'DEM-' + req.id }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {{ req.type }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{{ req.payload?.reason || req.description || 'Sans objet' }}</div>
                  <div class="text-xs text-gray-500" v-if="req.type === 'LEAVE'">
                    Du {{ req.payload?.start_date }} au {{ req.payload?.end_date }} ({{ req.payload?.leave_type }})
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ new Date(req.created_at).toLocaleDateString() }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusBadgeClass(req.status)" class="px-3 py-1 rounded-full text-xs font-medium uppercase">
                    {{ req.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <span class="text-gray-400 italic text-xs">Consultation</span>
                </td>
              </tr>
              <tr v-if="myRequests.length === 0">
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">Aucune demande trouvée.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2 class="text-xl font-bold mb-4 mt-4 text-gray-800">Les demandes par lesquelles je suis concerné</h2>
        <div class="bg-white rounded-2xl shadow-[0_15px_40px_rgba(127,7,28,0.10)] border border-red-100 overflow-x-auto mb-8">
          <table class="min-w-max w-full">
            <thead>
              <tr class="bg-gradient-to-r from-red-100/90 to-red-50 text-left">
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">ID</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Demandeur</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Type</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Détails / Raison</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Date de création</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Statut</th>
                <th class="px-6 py-4 text-sm font-semibold text-[#7f071c]">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="req in concerningRequests" :key="req.id" class="border-t border-red-100/80 hover:bg-red-50/70 transition">
                <td class="px-6 py-4 text-gray-600 font-medium">{{ req.reference || 'DEM-' + req.id }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-medium">
                  {{ req.requester_name || 'Utilisateur ' + req.requester_id }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {{ req.type }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{{ req.payload?.reason || req.description || 'Sans objet' }}</div>
                  <div class="text-xs text-gray-500" v-if="req.type === 'LEAVE'">
                    Du {{ req.payload?.start_date }} au {{ req.payload?.end_date }} ({{ req.payload?.leave_type }})
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ new Date(req.created_at).toLocaleDateString() }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusBadgeClass(req.status)" class="px-3 py-1 rounded-full text-xs font-medium uppercase">
                    {{ req.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div v-if="req.status === 'PENDING'" class="flex gap-2">
                    <button 
                      @click="updateStatus(req.id, 'APPROVED')"
                      class="text-emerald-600 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 px-3 py-1 rounded-lg transition"
                    >
                      Approuver
                    </button>
                    <button 
                      @click="openRejectModal(req.id)"
                      class="text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 px-3 py-1 rounded-lg transition"
                    >
                      Refuser
                    </button>
                  </div>
                  <span v-else class="text-gray-400 italic text-xs">Traitée</span>
                </td>
              </tr>
              <tr v-if="concerningRequests.length === 0">
                <td colspan="7" class="px-6 py-8 text-center text-gray-500">Aucune demande trouvée.</td>
              </tr>
            </tbody>
          </table>
        </div>

    <!-- Reject Modal -->
    <div v-if="rejectModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-96 shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Motif du refus</h2>
        <textarea v-model="rejectionComment" placeholder="Veuillez expliquer la raison du refus..." rows="3" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500"></textarea>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="rejectModalOpen = false" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">Annuler</button>
          <button @click="confirmReject" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg">Confirmer Refus</button>
        </div>
      </div>
    </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import api from '@/services/api';
import { useToast, useStatusBadges, useFormatters } from '@/composables';
import { getStoredProfile } from '@/services/session';

const toast = useToast();
const { getStatusBadgeClass } = useStatusBadges();
const { formatDate } = useFormatters();
const currentUser = getStoredProfile();

const requests = ref<any[]>([]);

const myRequests = computed(() => requests.value.filter(req => req.requester_id === currentUser?.id));
const concerningRequests = computed(() => requests.value.filter(req => req.requester_id !== currentUser?.id));

const rejectModalOpen = ref(false);
const rejectionComment = ref('');
const currentRejectId = ref<number | null>(null);

const fetchRequests = async () => {
  try {
    const res = await api.get('/requests/');
    requests.value = res.data.sort((a: any, b: any) => b.id - a.id);
  } catch (error) {
    console.error("Error fetching requests", error);
  }
};

const updateStatus = async (id: number, status: string, comment: string | null = null) => {
  try {
    await api.patch(`/requests/${id}/status`, {
      status: status,
      rejection_comment: comment
    });
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

onMounted(() => {
  fetchRequests();
});
</script>
