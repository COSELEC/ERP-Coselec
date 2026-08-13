<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold text-gray-800">Importer un fichier Excel</h2>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      <div 
        @dragover.prevent="isDragging = true" 
        @dragleave.prevent="isDragging = false" 
        @drop.prevent="handleDrop"
        :class="['border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors', isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:bg-gray-50']"
        @click="triggerFileInput"
      >
        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <div class="mt-4 flex text-sm text-gray-600 justify-center">
          <span class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
            Sélectionner un fichier
          </span>
          <p class="pl-1">ou glisser-déposer</p>
        </div>
        <p class="text-xs text-gray-500 mt-2">XLSX, XLS jusqu'à 10MB</p>
        <input ref="fileInput" type="file" class="hidden" accept=".xlsx, .xls" @change="handleFileSelect" />
      </div>

      <div v-if="selectedFile" class="mt-4 p-3 bg-gray-50 rounded text-sm text-gray-700 flex justify-between items-center">
        <span class="truncate">{{ selectedFile.name }}</span>
        <button @click="selectedFile = null" class="text-red-500 hover:text-red-700">Retirer</button>
      </div>
      
      <div class="mt-4 p-3 bg-blue-50 border border-blue-100 rounded-lg flex items-center justify-between">
        <div>
          <h4 class="text-sm font-medium text-blue-800">Besoin du modèle ?</h4>
          <p class="text-xs text-blue-600 mt-0.5">Téléchargez le format requis pour l'import.</p>
        </div>
        <button @click="downloadTemplate" class="text-xs bg-white text-blue-700 border border-blue-200 px-3 py-1.5 rounded hover:bg-blue-50 transition-colors flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">download</span> Modèle
        </button>
      </div>

      <div class="mt-6 flex justify-end space-x-3">
        <button @click="close" class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
          Annuler
        </button>
        <button 
          @click="uploadFile" 
          :disabled="!selectedFile || isLoading"
          class="inline-flex justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isLoading ? 'Importation...' : 'Importer' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '@/services/api';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'import']);

const isDragging = ref(false);
const selectedFile = ref(null);
const fileInput = ref(null);
const isLoading = ref(false);

const close = () => {
  selectedFile.value = null;
  emit('close');
};

const triggerFileInput = () => {
  fileInput.value.click();
};

const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
  }
};

const handleDrop = (event) => {
  isDragging.value = false;
  const file = event.dataTransfer.files[0];
  if (file) {
    selectedFile.value = file;
  }
};

const uploadFile = async () => {
  if (!selectedFile.value) return;
  
  isLoading.value = true;
  try {
    await emit('import', selectedFile.value);
    close();
  } catch (error) {
    console.error(error);
  } finally {
    isLoading.value = false;
  }
};

const downloadTemplate = async () => {
  try {
    const res = await api.get('/projects/import-template', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'Template_Import_Projet.xlsx');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error('Erreur lors du téléchargement du modèle', error);
  }
};
</script>
