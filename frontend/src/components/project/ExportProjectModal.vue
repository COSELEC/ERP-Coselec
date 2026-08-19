<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="close"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="close" />

        <!-- Panel -->
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
          <!-- Header -->
          <div class="bg-gradient-to-r from-[#d10f2f] to-[#97091f] px-6 py-5 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="bg-white/20 rounded-lg p-2">
                <span class="material-symbols-outlined text-white text-xl">download</span>
              </div>
              <div>
                <h2 class="text-white font-bold text-lg leading-tight">Exporter le Projet</h2>
                <p class="text-white/70 text-xs mt-0.5">Sélectionnez les éléments à exporter</p>
              </div>
            </div>
            <button
              @click="close"
              class="text-white/70 hover:text-white transition-colors rounded-lg p-1 hover:bg-white/10"
            >
              <span class="material-symbols-outlined text-xl">close</span>
            </button>
          </div>

          <!-- Body -->
          <div class="px-6 py-5 space-y-3">
            <!-- Select All -->
            <label class="flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all duration-200"
              :class="allSelected ? 'border-[#d10f2f] bg-red-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'">
              <input
                type="checkbox"
                :checked="allSelected"
                :indeterminate="someSelected && !allSelected"
                @change="toggleAll"
                class="w-4 h-4 rounded accent-[#d10f2f] cursor-pointer"
              />
              <div class="flex items-center gap-2 flex-1">
                <span class="material-symbols-outlined text-[#d10f2f] text-xl">select_all</span>
                <span class="font-semibold text-gray-800 text-sm">Tout sélectionner</span>
              </div>
            </label>

            <div class="border-t border-gray-100 pt-3 space-y-2">
              <!-- Gantt Option -->
              <label class="flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all duration-200"
                :class="options.gantt ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'">
                <input
                  type="checkbox"
                  v-model="options.gantt"
                  class="w-4 h-4 rounded accent-purple-600 cursor-pointer"
                />
                <div class="flex items-center gap-2 flex-1">
                  <span class="material-symbols-outlined text-purple-600 text-xl">event_note</span>
                  <div>
                    <p class="font-semibold text-gray-800 text-sm">Diagramme de Gantt</p>
                    <p class="text-xs text-gray-500">Planning des tâches et jalons (XLSX)</p>
                  </div>
                </div>
                <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">XLSX</span>
              </label>

              <!-- Budget Option -->
              <label class="flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all duration-200"
                :class="options.budget ? 'border-green-400 bg-green-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'">
                <input
                  type="checkbox"
                  v-model="options.budget"
                  class="w-4 h-4 rounded accent-green-600 cursor-pointer"
                />
                <div class="flex items-center gap-2 flex-1">
                  <span class="material-symbols-outlined text-green-600 text-xl">account_balance_wallet</span>
                  <div>
                    <p class="font-semibold text-gray-800 text-sm">Tableau Récap Contrat</p>
                    <p class="text-xs text-gray-500">Budget prestataires, décomptes & prix (XLSX)</p>
                  </div>
                </div>
                <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700">XLSX</span>
              </label>
            </div>

            <!-- No selection warning -->
            <Transition name="slide-down">
              <div v-if="showWarning" class="flex items-center gap-2 text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs">
                <span class="material-symbols-outlined text-base">warning</span>
                Veuillez sélectionner au moins un élément à exporter.
              </div>
            </Transition>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
            <button
              @click="close"
              class="px-5 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Annuler
            </button>
            <button
              @click="handleExport"
              :disabled="isExporting"
              class="px-5 py-2 text-sm font-semibold text-white bg-[#d10f2f] hover:bg-[#97091f] disabled:opacity-60 disabled:cursor-not-allowed rounded-lg transition-all duration-200 flex items-center gap-2 shadow-sm shadow-red-200"
            >
              <span v-if="isExporting" class="material-symbols-outlined text-base animate-spin">progress_activity</span>
              <span v-else class="material-symbols-outlined text-base">file_download</span>
              {{ isExporting ? 'Export en cours...' : 'Exporter' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import api from '@/services/api';
import { useToast } from '@/composables/useToast';

const props = defineProps<{
  isOpen: boolean;
  projectId: number | null;
  projectCode?: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const toast = useToast();

const options = ref({ gantt: false, budget: false });
const isExporting = ref(false);
const showWarning = ref(false);

// ── Computed ────────────────────────────────────────────────
const allSelected = computed(() => options.value.gantt && options.value.budget);
const someSelected = computed(() => options.value.gantt || options.value.budget);

// ── Helpers ─────────────────────────────────────────────────
const toggleAll = () => {
  const next = !allSelected.value;
  options.value.gantt = next;
  options.value.budget = next;
};

watch(someSelected, (val) => {
  if (val) showWarning.value = false;
});

// ── Close ────────────────────────────────────────────────────
const close = () => {
  if (isExporting.value) return;
  options.value = { gantt: false, budget: false };
  showWarning.value = false;
  emit('close');
};

// ── Download helper ──────────────────────────────────────────
const downloadBlob = (data: Blob, filename: string) => {
  const url = window.URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => window.URL.revokeObjectURL(url), 1000);
};

// ── Export ───────────────────────────────────────────────────
const handleExport = async () => {
  if (!someSelected.value) {
    showWarning.value = true;
    return;
  }
  if (!props.projectId) return;

  isExporting.value = true;
  const code = props.projectCode || props.projectId;
  const both = options.value.gantt && options.value.budget;

  try {
    if (both) {
      // Single file, two sheets
      await api
        .get(`/projects/${props.projectId}/export-combined`, { responseType: 'blob' })
        .then(res => downloadBlob(new Blob([res.data]), `Export_${code}.xlsx`))
        .catch(() => toast.error("Erreur lors de l'export combiné."));
    } else {
      // Individual file(s)
      const tasks: Promise<void>[] = [];

      if (options.value.gantt) {
        tasks.push(
          api.get(`/projects/${props.projectId}/export-gantt`, { responseType: 'blob' })
            .then(res => downloadBlob(new Blob([res.data]), `Gantt_${code}.xlsx`))
            .catch(() => toast.error("Erreur lors de l'export du Gantt."))
        );
      }

      if (options.value.budget) {
        tasks.push(
          api.get(`/projects/${props.projectId}/export-budget`, { responseType: 'blob' })
            .then(res => downloadBlob(new Blob([res.data]), `Budget_${code}.xlsx`))
            .catch(() => toast.error("Erreur lors de l'export du Budget."))
        );
      }

      await Promise.all(tasks);
    }

    toast.success('Export terminé avec succès.');
    close();
  } finally {
    isExporting.value = false;
  }
};
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .relative,
.modal-fade-leave-active .relative {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-fade-enter-from .relative {
  transform: scale(0.95) translateY(-8px);
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* Custom checkbox indeterminate state */
input[type="checkbox"]:indeterminate {
  accent-color: #d10f2f;
}
</style>
