<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
      <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
        <h2 class="text-xl font-bold flex items-center gap-2">
          <span class="material-symbols-outlined">add_chart</span>
          Créer {{ mode === 'processus' ? 'un Processus' : 'un Indicateur' }}
        </h2>
        <button @click="$emit('close')" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <!-- Mode Selector -->
        <div class="flex gap-4 mb-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" v-model="mode" value="processus" class="text-red-600 focus:ring-red-500" />
            <span class="text-sm font-medium text-gray-700">Processus</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" v-model="mode" value="indicator" class="text-red-600 focus:ring-red-500" />
            <span class="text-sm font-medium text-gray-700">Indicateur</span>
          </label>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
          <input 
            v-model="name"
            type="text" 
            required
            class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
          />
        </div>

        <div v-if="mode === 'processus'">
          <label class="block text-sm font-medium text-gray-700 mb-1">Direction / Département (Optionnel)</label>
          <select 
            v-model="department_id"
            class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
          >
            <option value="">-- Aucun --</option>
            <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
          </select>
          <p class="text-xs text-gray-500 mt-1">Lier ce processus à une direction permet à ses Pilotes/Copilotes d'en éditer les valeurs.</p>
        </div>

        <div v-if="mode === 'indicator'">
          <label class="block text-sm font-medium text-gray-700 mb-1">Processus Parent</label>
          <select 
            v-model="processus_id"
            required
            class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
          >
            <option value="" disabled>Sélectionner un processus</option>
            <option v-for="proc in processusList" :key="proc.id" :value="proc.id">{{ proc.name }}</option>
          </select>
        </div>

        <div class="mt-8 flex justify-end gap-3">
          <button 
            type="button" 
            @click="$emit('close')" 
            class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition"
          >
            Annuler
          </button>
          <button 
            type="submit" 
            :disabled="loading"
            class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition disabled:opacity-50 flex items-center gap-2"
          >
            <span v-if="loading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
            Créer
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { kpiService, type KPIProcessus } from '@/services/kpi';
import api from '@/services/api';
import { useToast } from '@/composables/useToast';

const props = defineProps<{
  processusList: KPIProcessus[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'created'): void;
}>();

const toast = useToast();
const mode = ref<'processus' | 'indicator'>('processus');
const name = ref('');
const department_id = ref<number | ''>('');
const processus_id = ref<number | ''>('');
const loading = ref(false);

const departments = ref<any[]>([]);

onMounted(async () => {
  try {
    const res = await api.get('/departments');
    departments.value = res.data;
  } catch (e) {
    console.error("Error fetching departments", e);
  }
});

const handleSubmit = async () => {
  loading.value = true;
  try {
    if (mode.value === 'processus') {
      await kpiService.createProcessus(name.value, department_id.value === '' ? null : Number(department_id.value));
      toast.success("Processus créé avec succès");
    } else {
      await kpiService.createIndicator(name.value, Number(processus_id.value));
      toast.success("Indicateur créé avec succès");
    }
    emit('created');
  } catch (e: any) {
    const msg = e.response?.data?.detail || "Erreur lors de la création";
    toast.error(msg);
  } finally {
    loading.value = false;
  }
};
</script>
