<script setup lang="ts">
import { ref, computed } from 'vue';
import { kpiService } from '@/services/kpi';
import { useToast } from '@/composables/useToast';

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'imported'): void;
}>();

const toast = useToast();

const step = ref<1 | 2>(1);
const loading = ref(false);

const file = ref<File | null>(null);
const sheetNames = ref<string[]>([]);
const selectedSheet = ref<string>('');

const selectedYear = ref<number>(new Date().getFullYear());
const selectedMonthIndex = ref<number>(new Date().getMonth() + 1);

const months = [
  { value: 1, name: 'janv', colName: `janv-${selectedYear.value.toString().slice(-2)}` },
  { value: 2, name: 'févr', colName: `févr-${selectedYear.value.toString().slice(-2)}` },
  { value: 3, name: 'mars', colName: `mars-${selectedYear.value.toString().slice(-2)}` },
  { value: 4, name: 'avr', colName: `avr-${selectedYear.value.toString().slice(-2)}` },
  { value: 5, name: 'mai', colName: `mai-${selectedYear.value.toString().slice(-2)}` },
  { value: 6, name: 'juin', colName: `juin-${selectedYear.value.toString().slice(-2)}` },
  { value: 7, name: 'juil', colName: `juil-${selectedYear.value.toString().slice(-2)}` },
  { value: 8, name: 'août', colName: `août-${selectedYear.value.toString().slice(-2)}` },
  { value: 9, name: 'sept', colName: `sept-${selectedYear.value.toString().slice(-2)}` },
  { value: 10, name: 'oct', colName: `oct-${selectedYear.value.toString().slice(-2)}` },
  { value: 11, name: 'nov', colName: `nov-${selectedYear.value.toString().slice(-2)}` },
  { value: 12, name: 'déc', colName: `déc-${selectedYear.value.toString().slice(-2)}` },
];

const getMonthOptions = computed(() => {
  const yrStr = selectedYear.value.toString().slice(-2);
  return [
    { value: 1, label: `Janvier (janv-${yrStr})`, col: `janv-${yrStr}` },
    { value: 2, label: `Février (févr-${yrStr})`, col: `févr-${yrStr}` },
    { value: 3, label: `Mars (mars-${yrStr})`, col: `mars-${yrStr}` },
    { value: 4, label: `Avril (avr-${yrStr})`, col: `avr-${yrStr}` },
    { value: 5, label: `Mai (mai-${yrStr})`, col: `mai-${yrStr}` },
    { value: 6, label: `Juin (juin-${yrStr})`, col: `juin-${yrStr}` },
    { value: 7, label: `Juillet (juil-${yrStr})`, col: `juil-${yrStr}` },
    { value: 8, label: `Août (août-${yrStr})`, col: `août-${yrStr}` },
    { value: 9, label: `Septembre (sept-${yrStr})`, col: `sept-${yrStr}` },
    { value: 10, label: `Octobre (oct-${yrStr})`, col: `oct-${yrStr}` },
    { value: 11, label: `Novembre (nov-${yrStr})`, col: `nov-${yrStr}` },
    { value: 12, label: `Décembre (déc-${yrStr})`, col: `déc-${yrStr}` },
  ];
});

const handleFileDrop = (e: DragEvent) => {
  e.preventDefault();
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    file.value = e.dataTransfer.files[0];
  }
};

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    file.value = target.files[0];
  }
};

const nextStep = async () => {
  if (!file.value) return;
  loading.value = true;
  try {
    sheetNames.value = await kpiService.uploadPreview(file.value);
    if (sheetNames.value.length > 0) {
      selectedSheet.value = sheetNames.value[0];
      step.value = 2;
    }
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Erreur lors de la lecture du fichier Excel");
  } finally {
    loading.value = false;
  }
};

const submitImport = async () => {
  if (!file.value || !selectedSheet.value) return;
  
  loading.value = true;
  try {
    const selectedMonthObj = getMonthOptions.value.find(m => m.value === selectedMonthIndex.value);
    if (!selectedMonthObj) return;

    const res = await kpiService.uploadParse(
      file.value,
      selectedSheet.value,
      selectedYear.value,
      selectedMonthObj.col,
      selectedMonthIndex.value
    );
    toast.success(res.message);
    emit('imported');
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Erreur lors de l'importation");
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
        <h2 class="text-xl font-bold text-gray-900">
          {{ step === 1 ? '1. Charger le fichier Excel' : '2. Configuration de l\'import' }}
        </h2>
        <button 
          @click="emit('close')"
          class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-colors"
        >
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- Body -->
      <div class="p-6">
        <!-- Step 1: File Selection -->
        <div v-if="step === 1" class="space-y-4">
          <p class="text-sm text-gray-600">Sélectionnez le fichier Excel contenant le suivi des KPI.</p>
          
          <div 
            @dragover.prevent
            @drop="handleFileDrop"
            class="flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl hover:bg-gray-50 transition-colors relative"
            :class="{'border-[#d10f2f] bg-red-50/30': file}"
          >
            <div class="space-y-2 text-center">
              <span 
                class="material-symbols-outlined text-4xl"
                :class="file ? 'text-[#d10f2f]' : 'text-gray-400'"
              >
                {{ file ? 'table_view' : 'cloud_upload' }}
              </span>
              
              <div class="flex text-sm text-gray-600 justify-center">
                <label class="relative cursor-pointer rounded-md bg-transparent font-medium text-[#d10f2f] focus-within:outline-none hover:text-[#a80c26]">
                  <span>{{ file ? file.name : "Téléverser un fichier" }}</span>
                  <input type="file" class="sr-only" @change="handleFileSelect" accept=".xls,.xlsx" />
                </label>
                <p class="pl-1" v-if="!file">ou glisser-déposer</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Configuration -->
        <div v-else-if="step === 2" class="space-y-4">
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Feuille Excel
            </label>
            <select 
              v-model="selectedSheet"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-[#d10f2f] focus:border-[#d10f2f]"
            >
              <option v-for="sheet in sheetNames" :key="sheet" :value="sheet">
                {{ sheet }}
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">Exemple : "KPI 2026 COSELEC"</p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Année
              </label>
              <input 
                type="number"
                v-model="selectedYear"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-[#d10f2f] focus:border-[#d10f2f]"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Mois (Colonne cible)
              </label>
              <select 
                v-model="selectedMonthIndex"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-[#d10f2f] focus:border-[#d10f2f]"
              >
                <option v-for="m in getMonthOptions" :key="m.value" :value="m.value">
                  {{ m.label }}
                </option>
              </select>
            </div>
          </div>
          
          <div class="bg-blue-50 text-blue-800 p-3 rounded-lg text-sm flex gap-2">
            <span class="material-symbols-outlined text-xl">info</span>
            <p>Le système cherchera la colonne nommée très exactement <b>{{ getMonthOptions.find(m => m.value === selectedMonthIndex)?.col }}</b>. Si elle porte un autre nom, l'import échouera.</p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end gap-3">
        <button 
          v-if="step === 2"
          @click="step = 1"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          :disabled="loading"
        >
          Retour
        </button>
        <button 
          v-else
          @click="emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Annuler
        </button>
        
        <button 
          v-if="step === 1"
          @click="nextStep"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#d10f2f] rounded-lg hover:bg-[#a80c26] transition-colors disabled:opacity-50"
          :disabled="!file || loading"
        >
          <span v-if="loading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
          Continuer
        </button>
        <button 
          v-else
          @click="submitImport"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#d10f2f] rounded-lg hover:bg-[#a80c26] transition-colors disabled:opacity-50"
          :disabled="loading"
        >
          <span v-if="loading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
          {{ loading ? 'Importation...' : 'Importer' }}
        </button>
      </div>
    </div>
  </div>
</template>
