<template>
  <form @submit.prevent="submitFuelRequest" class="space-y-6">
    <div class="rounded-2xl border border-red-100 bg-red-50/40 p-4">
      <div class="flex items-center gap-3">
        <span class="material-symbols-outlined text-red-600 text-2xl">local_gas_station</span>
        <div>
          <h3 class="text-base font-bold text-gray-900">Demande de Carburant (DMCAR)</h3>
          <p class="text-xs text-gray-500">Pour tout déplacement professionnel nécessitant un approvisionnement en carburant.</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">Date de la demande *</label>
        <input 
          type="date" 
          v-model="form.request_date" 
          required 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">Projet concerné (Optionnel)</label>
        <select 
          v-model="form.project_id" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100"
        >
          <option :value="null">-- Aucun / Déplacement général --</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">N° Affaire (Optionnel)</label>
        <input 
          type="text" 
          v-model="form.affaire_no" 
          placeholder="Ex: AFF-2026-042" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">N° Dossier (Optionnel)</label>
        <input 
          type="text" 
          v-model="form.dossier_no" 
          placeholder="Ex: DOS-012" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div class="md:col-span-2">
        <label class="mb-2 block text-sm font-semibold text-gray-700">Objet du Déplacement *</label>
        <input 
          type="text" 
          v-model="form.objet_deplacement" 
          required 
          placeholder="Ex: Déplacement sur le chantier Oujda pour supervision" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">Matricule Véhicule *</label>
        <input 
          type="text" 
          v-model="form.vehicule_matricule" 
          required 
          placeholder="Ex: 12345-A-6" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">Destination *</label>
        <input 
          type="text" 
          v-model="form.destination" 
          required 
          placeholder="Ex: Chantier Agadir" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">Relevé Kilométrique (Km) *</label>
        <input 
          type="number" 
          v-model.number="form.releve_kilometrique" 
          min="1" 
          required 
          placeholder="Ex: 84500" 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-semibold text-gray-700">Nombre de jours *</label>
        <input 
          type="number" 
          v-model.number="form.nombre_jours" 
          min="1" 
          required 
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" 
        />
      </div>

      <div class="md:col-span-2">
        <label class="mb-2 block text-sm font-semibold text-gray-700">Quantité de carburant (Litres) *</label>
        <div class="relative">
          <input 
            type="number" 
            step="0.1" 
            v-model.number="form.quantite_carburant" 
            min="0.1" 
            required 
            placeholder="Ex: 45" 
            class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 pr-12 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100 font-bold" 
          />
          <span class="absolute right-4 top-3 text-gray-500 font-bold text-sm">L</span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-100">
      <button 
        type="submit" 
        :disabled="isSubmitting"
        class="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-red-200 transition hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span v-if="isSubmitting" class="animate-spin material-symbols-outlined text-[18px]">sync</span>
        <span v-else class="material-symbols-outlined text-[18px]">send</span>
        {{ isSubmitting ? "Envoi en cours..." : "Envoyer la demande de carburant" }}
      </button>
      
      <button 
        type="button" 
        @click="resetForm"
        class="inline-flex items-center gap-2 rounded-2xl border border-red-100 bg-white px-5 py-3 text-sm font-semibold text-red-700 transition hover:bg-red-50"
      >
        Réinitialiser
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { useToast } from '@/composables/useToast';

const emit = defineEmits(['submitted']);

const router = useRouter();
const toast = useToast();
const isSubmitting = ref(false);
const projects = ref<any[]>([]);

const getInitialForm = () => ({
  request_date: new Date().toISOString().split('T')[0],
  project_id: null as number | null,
  affaire_no: '',
  dossier_no: '',
  vehicule_matricule: '',
  objet_deplacement: '',
  destination: '',
  releve_kilometrique: null as number | null,
  nombre_jours: 1,
  quantite_carburant: null as number | null,
});

const form = reactive(getInitialForm());

onMounted(async () => {
  try {
    const res = await api.get('/projects/');
    projects.value = res.data || [];
  } catch (error) {
    console.error("Error loading projects", error);
  }
});

const resetForm = () => {
  Object.assign(form, getInitialForm());
};

const submitFuelRequest = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;

  try {
    await api.post('/requests/', {
      type: 'FUEL',
      project_id: form.project_id || null,
      description: form.objet_deplacement || 'Demande de carburant',
      payload: {
        type: 'FUEL',
        request_date: form.request_date,
        vehicle_plate: form.vehicule_matricule,
        destination: form.destination,
        fuel_quantity: parseFloat(String(form.quantite_carburant)) || 1,
        trip_days: parseInt(String(form.nombre_jours)) || 1,
        odometer_reading: parseInt(String(form.releve_kilometrique)) || 1,
        trip_purpose: form.objet_deplacement,
        affaire_no: form.affaire_no || undefined,
        dossier_no: form.dossier_no || undefined,
      }
    });

    toast.success('Demande de carburant créée avec succès !');
    resetForm();
    emit('submitted');
    router.push('/admin/requests?category=fuel');
  } catch (error: any) {
    console.error('Erreur création demande carburant', error);
    toast.error(error.response?.data?.detail || 'Impossible de créer la demande pour le moment.');
  } finally {
    isSubmitting.value = false;
  }
};
</script>
