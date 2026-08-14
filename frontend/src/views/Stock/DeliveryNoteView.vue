<template>
  <div class="p-8 max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-3xl font-bold text-gray-900">Bons de Livraison</h1>
        <p class="text-sm text-gray-500">Vérification et validation des réceptions</p>
    </div>
    
    <div v-if="loading" class="flex justify-center p-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-red-500">sync</span>
    </div>
    
    <div v-else class="grid gap-6">
        <div v-for="note in deliveryNotes" :key="note.id" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="p-6 border-b border-gray-100 flex justify-between items-start bg-gray-50">
                <div>
                    <h2 class="text-xl font-bold text-gray-800">{{ note.reference }}</h2>
                    <p class="text-sm text-gray-500 mt-1">Fournisseur: {{ note.supplier_name || 'N/A' }} | PO: {{ note.purchase_order_id }}</p>
                </div>
                <div class="flex items-center space-x-4">
                    <span :class="getStatusClass(note.status)" class="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                        {{ note.status }}
                    </span>
                    <button v-if="canValidate(note)" @click="openModal(note)" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center shadow-sm">
                        <span class="material-symbols-outlined text-[18px] mr-2">edit_document</span>
                        Contrôler
                    </button>
                </div>
            </div>
            
            <div class="p-6">
                <table class="w-full text-sm text-left">
                    <thead class="text-xs text-gray-500 bg-gray-50 uppercase font-semibold">
                        <tr>
                            <th class="px-4 py-3 rounded-l-lg">Désignation</th>
                            <th class="px-4 py-3">Qté Cmd</th>
                            <th class="px-4 py-3">Qté Livrée</th>
                            <th class="px-4 py-3 text-center">Conformité</th>
                            <th class="px-4 py-3 rounded-r-lg">Remarques</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        <tr v-for="line in note.lines" :key="line.id" class="hover:bg-gray-50/50">
                            <td class="px-4 py-3 font-medium text-gray-900">{{ line.designation }}</td>
                            <td class="px-4 py-3 text-gray-600">{{ line.ordered_quantity }}</td>
                            <td class="px-4 py-3 text-gray-900 font-bold">{{ line.delivered_quantity }}</td>
                            <td class="px-4 py-3 text-center">
                                <span v-if="line.is_compliant" class="material-symbols-outlined text-green-500">check_circle</span>
                                <span v-else class="material-symbols-outlined text-red-500">cancel</span>
                            </td>
                            <td class="px-4 py-3 text-gray-500 text-xs">{{ line.notes || '-' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div v-if="deliveryNotes.length === 0" class="text-center p-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <span class="material-symbols-outlined text-4xl text-gray-400 mb-2">inventory_2</span>
            <h3 class="text-lg font-medium text-gray-900">Aucun bon de livraison</h3>
            <p class="text-gray-500">Il n'y a pas de bons de livraison en attente pour le moment.</p>
        </div>
    </div>
    
    <!-- Modal for Validation -->
    <div v-if="showModal && selectedNote" class="fixed inset-0 z-50 overflow-y-auto bg-gray-900/50 backdrop-blur-sm flex justify-center items-center p-4">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div class="p-6 border-b border-gray-100 flex justify-between items-center sticky top-0 bg-white rounded-t-2xl z-10">
                <h3 class="text-xl font-bold text-gray-900">Contrôle Réception: {{ selectedNote.reference }}</h3>
                <button @click="showModal = false" class="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            
            <div class="p-6 overflow-y-auto flex-1 space-y-6">
                <div class="grid gap-4">
                    <div v-for="(line, idx) in editLines" :key="idx" class="p-4 bg-gray-50 border border-gray-200 rounded-xl flex flex-wrap gap-4 items-end">
                        <div class="flex-1 min-w-[200px]">
                            <label class="text-xs font-semibold text-gray-600 block mb-1">Désignation</label>
                            <div class="px-3 py-2 bg-white rounded-lg border border-gray-200 text-sm text-gray-700">{{ line.designation }}</div>
                        </div>
                        <div class="w-24">
                            <label class="text-xs font-semibold text-gray-600 block mb-1">Qté Cmd</label>
                            <div class="px-3 py-2 bg-white rounded-lg border border-gray-200 text-sm text-gray-500">{{ line.ordered_quantity }}</div>
                        </div>
                        <div class="w-32">
                            <label class="text-xs font-bold text-blue-600 block mb-1">Qté Livrée *</label>
                            <input v-model.number="line.delivered_quantity" type="number" min="0" :disabled="!isMagasinierAction" class="w-full rounded-lg border border-blue-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-medium" />
                        </div>
                        <div class="w-24 flex flex-col items-center">
                            <label class="text-xs font-bold text-blue-600 block mb-3">Conforme *</label>
                            <input v-model="line.is_compliant" type="checkbox" :disabled="!isMagasinierAction" class="h-5 w-5 rounded border-blue-300 text-blue-600 focus:ring-blue-500" />
                        </div>
                        <div class="flex-1 min-w-[150px]">
                            <label class="text-xs font-semibold text-gray-600 block mb-1">Remarques</label>
                            <input v-model="line.notes" type="text" placeholder="Observations..." :disabled="!isMagasinierAction" class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-400 focus:ring-2 focus:ring-red-100" />
                        </div>
                    </div>
                </div>
                
                <div v-if="!isMagasinierAction">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Commentaire d'approbation (Chef de projet)</label>
                    <textarea v-model="approvalComments" rows="3" class="w-full rounded-xl border border-gray-300 p-3 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-200"></textarea>
                </div>
            </div>
            
            <div class="p-6 border-t border-gray-100 flex justify-end gap-3 sticky bottom-0 bg-white rounded-b-2xl z-10">
                <button @click="showModal = false" class="px-6 py-2.5 rounded-xl font-medium text-gray-600 hover:bg-gray-100 transition-colors">Annuler</button>
                <button @click="submitValidation" :disabled="isSubmitting" class="bg-red-600 hover:bg-red-700 text-white px-8 py-2.5 rounded-xl font-bold shadow-md shadow-red-200 transition-all flex items-center gap-2">
                    <span v-if="isSubmitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                    <span v-else class="material-symbols-outlined text-[18px]">done_all</span>
                    {{ isMagasinierAction ? 'Valider la réception' : 'Approuver' }}
                </button>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';
import { getStoredProfile, hasAnyRole } from '@/services/session';
import { useToast, useStatusBadges } from '@/composables';

const profile = getStoredProfile();
const toast = useToast();
const { getStatusBadgeClass: getStatusClass } = useStatusBadges();

const loading = ref(true);
const deliveryNotes = ref<any[]>([]);

const showModal = ref(false);
const selectedNote = ref<any>(null);
const editLines = ref<any[]>([]);
const approvalComments = ref('');
const isSubmitting = ref(false);

const roles = computed(() => profile?.roles || []);
const isMagasinier = computed(() => hasAnyRole(roles.value, ['Admin', 'Stock / Logistique', 'Magasinier']));
const isManager = computed(() => hasAnyRole(roles.value, ['Admin', 'Chef de Projet', 'Direction']));

const fetchNotes = async () => {
    loading.value = true;
    try {
        const res = await api.get('/procurement/delivery-notes');
        deliveryNotes.value = res.data;
    } catch (error) {
        console.error(error);
        toast.error('Erreur lors du chargement des bons de livraison');
    } finally {
        loading.value = false;
    }
};

onMounted(fetchNotes);

const canValidate = (note: any) => {
    if (note.status === 'DRAFT' && isMagasinier.value) return true;
    if (note.status === 'CHECKED_BY_MAGASINIER' && isManager.value) return true;
    return false;
};

const isMagasinierAction = computed(() => {
    return selectedNote.value?.status === 'DRAFT';
});

const openModal = (note: any) => {
    selectedNote.value = note;
    editLines.value = note.lines.map((l: any) => ({ ...l }));
    approvalComments.value = '';
    showModal.value = true;
};

const submitValidation = async () => {
    if (!selectedNote.value) return;
    isSubmitting.value = true;
    
    const payload = {
        lines: editLines.value,
        comments: approvalComments.value,
        action: isMagasinierAction.value ? 'magasinier' : 'manager'
    };
    
    try {
        await api.post(`/procurement/delivery-notes/${selectedNote.value.id}/validate`, payload);
        toast.success('Bon de livraison mis à jour avec succès');
        showModal.value = false;
        fetchNotes();
    } catch (error) {
        console.error(error);
        toast.error('Erreur lors de la validation');
    } finally {
        isSubmitting.value = false;
    }
};
</script>
