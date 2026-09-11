<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
      <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center shrink-0">
        <h2 class="text-xl font-bold flex items-center gap-2">
          <span class="material-symbols-outlined">edit_square</span>
          Renseigner KPI
        </h2>
        <button @click="$emit('close')" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      
      <div class="px-6 py-4 border-b border-gray-100 bg-gray-50 shrink-0">
        <h3 class="font-bold text-gray-900">{{ indicator.name }}</h3>
        <p class="text-sm text-gray-500">Année {{ year }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 flex-1 overflow-y-auto">
        <div class="space-y-4">
          <div v-for="(month, idx) in months" :key="idx" class="flex items-center gap-4">
            <span class="w-20 text-sm font-medium text-gray-700">{{ month.name }}</span>
            <input 
              v-model="formData[idx].value_raw"
              type="text" 
              placeholder="Valeur"
              class="flex-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
            />
            <input 
              v-model.number="formData[idx].value_numeric"
              type="number" 
              step="any"
              placeholder="Numérique"
              class="flex-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
            />
          </div>
        </div>

        <div class="mt-8 flex justify-end gap-3 pt-4 border-t sticky bottom-0 bg-white">
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
            Enregistrer
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { kpiService, type KPIIndicator } from '@/services/kpi';
import { useToast } from '@/composables/useToast';

const props = defineProps<{
  indicator: KPIIndicator;
  year: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const toast = useToast();
const loading = ref(false);

const months = [
  { index: 1, name: 'Janvier' },
  { index: 2, name: 'Février' },
  { index: 3, name: 'Mars' },
  { index: 4, name: 'Avril' },
  { index: 5, name: 'Mai' },
  { index: 6, name: 'Juin' },
  { index: 7, name: 'Juillet' },
  { index: 8, name: 'Août' },
  { index: 9, name: 'Septembre' },
  { index: 10, name: 'Octobre' },
  { index: 11, name: 'Novembre' },
  { index: 12, name: 'Décembre' }
];

const formData = ref(Array.from({ length: 12 }, () => ({
  value_raw: '',
  value_numeric: null as number | null
})));

onMounted(() => {
  // Pre-fill existing values
  props.indicator.values.forEach(v => {
    if (v.year === props.year && v.month >= 1 && v.month <= 12) {
      formData.value[v.month - 1].value_raw = v.value_raw || '';
      formData.value[v.month - 1].value_numeric = v.value_numeric;
    }
  });
});

const handleSubmit = async () => {
  loading.value = true;
  try {
    const promises = [];
    for (let i = 0; i < 12; i++) {
      const fd = formData.value[i];
      if (fd && (fd.value_raw !== '' || fd.value_numeric !== null)) {
        promises.push(kpiService.updateKpiValue(
          props.indicator.id,
          props.year,
          i + 1,
          fd.value_raw,
          fd.value_numeric
        ));
      }
    }
    
    await Promise.all(promises);
    toast.success("Valeurs enregistrées avec succès");
    emit('saved');
  } catch (e: any) {
    const msg = e.response?.data?.detail || "Erreur lors de l'enregistrement";
    toast.error(msg);
  } finally {
    loading.value = false;
  }
};
</script>
