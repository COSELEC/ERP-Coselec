<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
    <div class="bg-white rounded-3xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]">
      
      <!-- Header -->
      <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span class="material-symbols-outlined text-[#d10f2f]">attach_file</span>
          Pièces Jointes {{ type === 'bank' ? 'Banque' : 'Caisse' }} (#{{ voucherId }})
        </h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 overflow-y-auto flex-1 space-y-8">
        
        <!-- Upload Section -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-3">Ajouter un document (Chèque, reçu, facture...)</label>
          <div 
            class="border-2 border-dashed border-gray-200 rounded-2xl p-8 text-center bg-gray-50 hover:bg-red-50 hover:border-red-200 transition-colors cursor-pointer relative"
            @click="$refs.fileInput.click()"
            @dragover.prevent="dragover = true"
            @dragleave.prevent="dragover = false"
            @drop.prevent="handleDrop"
            :class="{'border-red-400 bg-red-50': dragover}"
          >
            <input type="file" ref="fileInput" class="hidden" @change="handleFileSelect" accept="image/*,application/pdf" multiple />
            
            <span class="material-symbols-outlined text-4xl text-gray-400 mb-2">cloud_upload</span>
            <p class="text-sm text-gray-600 font-medium">Cliquez ou glissez-déposez vos fichiers ici</p>
            <p class="text-xs text-gray-400 mt-1">PNG, JPG, PDF jusqu'à 10MB</p>
            
            <!-- Uploading state -->
            <div v-if="isUploading" class="absolute inset-0 bg-white/80 rounded-2xl flex items-center justify-center backdrop-blur-[2px]">
              <div class="flex items-center gap-2 text-[#d10f2f] font-semibold">
                <span class="material-symbols-outlined animate-spin">refresh</span>
                Envoi en cours...
              </div>
            </div>
          </div>
        </div>

        <!-- Gallery Section -->
        <div>
          <h3 class="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[18px]">photo_library</span>
            Fichiers joints ({{ attachments.length }})
          </h3>
          
          <div v-if="isLoading" class="flex justify-center py-8">
            <span class="material-symbols-outlined animate-spin text-3xl text-gray-300">refresh</span>
          </div>
          
          <div v-else-if="attachments.length === 0" class="text-center py-8 bg-gray-50 rounded-2xl border border-gray-100 border-dashed">
            <span class="material-symbols-outlined text-3xl text-gray-300 mb-2">image_not_supported</span>
            <p class="text-sm text-gray-500">Aucune pièce jointe pour le moment.</p>
          </div>

          <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <div 
              v-for="att in attachments" 
              :key="att.id"
              class="group relative aspect-square rounded-xl overflow-hidden border border-gray-200 bg-gray-50 shadow-sm hover:shadow-md transition-all cursor-pointer"
              @click="openPreview(att.url)"
            >
              <!-- PDF Preview -->
              <div v-if="att.mime_type === 'application/pdf'" class="w-full h-full flex flex-col items-center justify-center bg-red-50 text-red-600">
                <span class="material-symbols-outlined text-4xl mb-2">picture_as_pdf</span>
                <span class="text-xs font-bold px-2 text-center truncate w-full">{{ att.file_name }}</span>
              </div>
              
              <!-- Image Preview -->
              <img v-else :src="att.url" :alt="att.file_name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
              
              <!-- Hover Overlay -->
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[1px]">
                <span class="material-symbols-outlined text-white text-3xl drop-shadow-md">visibility</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { api } from '@/services/api';
import { useToast } from '@/composables/useToast';

const props = defineProps({
  isOpen: Boolean,
  voucherId: Number,
  type: {
    type: String,
    validator: (v) => ['bank', 'caisse'].includes(v)
  }
});

const emit = defineEmits(['close']);

const toast = useToast();
const dragover = ref(false);
const isUploading = ref(false);
const isLoading = ref(false);
const attachments = ref([]);
const fileInput = ref(null);

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.voucherId) {
    fetchAttachments();
  } else {
    attachments.value = [];
  }
});

const close = () => {
  emit('close');
};

const getEndpoint = () => {
  return props.type === 'bank' 
    ? `/bank-vouchers/${props.voucherId}/attachments`
    : `/caisse/${props.voucherId}/attachments`;
};

const fetchAttachments = async () => {
  isLoading.value = true;
  try {
    const res = await api.get(getEndpoint());
    attachments.value = res.data;
  } catch (error) {
    console.error("Error fetching attachments", error);
    toast.error("Erreur lors de la récupération des pièces jointes");
  } finally {
    isLoading.value = false;
  }
};

const handleFileSelect = (e) => {
  if (e.target.files.length) {
    uploadFiles(e.target.files);
  }
};

const handleDrop = (e) => {
  dragover.value = false;
  if (e.dataTransfer.files.length) {
    uploadFiles(e.dataTransfer.files);
  }
};

const uploadFiles = async (files) => {
  isUploading.value = true;
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await api.post(getEndpoint(), formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success(`Fichier ${file.name} envoyé !`);
    } catch (error) {
      console.error("Upload error", error);
      toast.error(`Erreur lors de l'envoi de ${file.name}`);
    }
  }
  
  await fetchAttachments();
  
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  isUploading.value = false;
};

const openPreview = (url) => {
  window.open(url, '_blank');
};
</script>
