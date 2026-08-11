<script setup lang="ts">
import { ref, watch } from 'vue';
import { documentService, type EmployeeDocument } from '@/services/documents';

const props = defineProps<{
  employeeId: number;
}>();

const documents = ref<EmployeeDocument[]>([]);
const loading = ref(true);
const uploading = ref(false);
const downloadingDocumentId = ref<number | null>(null);
const errorMessage = ref('');
const showForm = ref(false);

const fileInput = ref<HTMLInputElement | null>(null);

const form = ref({
  category: 'Identité',
  numero: '',
  expiry_date: ''
});
const selectedFile = ref<File | null>(null);

const loadDocuments = async () => {
  if (!props.employeeId) return;
  try {
    loading.value = true;
    documents.value = await documentService.getByEmployee(props.employeeId);
  } catch (error) {
    errorMessage.value = "Erreur lors du chargement des documents.";
  } finally {
    loading.value = false;
  }
};

watch(() => props.employeeId, () => {
  loadDocuments();
}, { immediate: true });

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] || null;
  } else {
    selectedFile.value = null;
  }
};

const handleSubmit = async () => {
  if (!selectedFile.value) {
    errorMessage.value = "Veuillez sélectionner un fichier.";
    return;
  }

  try {
    uploading.value = true;
    errorMessage.value = '';
    
    await documentService.upload(
      props.employeeId,
      selectedFile.value,
      form.value.category,
      form.value.numero || undefined,
      form.value.expiry_date || undefined
    );

    showForm.value = false;
    form.value = { category: 'Identité', numero: '', expiry_date: '' };
    selectedFile.value = null;
    if (fileInput.value) fileInput.value.value = ''; 
    
    await loadDocuments();
  } catch (error) {
    errorMessage.value = "Échec de l'upload du document.";
    console.error(error);
  } finally {
    uploading.value = false;
  }
};

const handleDownload = async (doc: EmployeeDocument) => {
  try {
    downloadingDocumentId.value = doc.id;
    errorMessage.value = '';
    await documentService.download(doc.id, doc.file_name);
  } catch (error) {
    errorMessage.value = "Échec du téléchargement du document.";
    console.error(error);
  } finally {
    downloadingDocumentId.value = null;
  }
};

const handleDelete = async (id: number) => {
  if (confirm('Voulez-vous vraiment supprimer ce document ?')) {
    try {
      await documentService.delete(id);
      await loadDocuments();
    } catch (error) {
      console.error(error);
    }
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'Identité': return 'badge';
    case 'Contrat': return 'description';
    case 'Social/Familial': return 'family_history';
    default: return 'folder';
  }
};
</script>

<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <span class="material-symbols-outlined text-[#d10f2f]">folder_managed</span>
        <span>Documents & Pièces jointes</span>
      </h3>
      <button 
        @click="showForm = !showForm"
        class="inline-flex items-center gap-2 rounded-xl bg-[#d10f2f] px-3.5 py-2 text-xs font-semibold text-white shadow-lg shadow-red-100 transition hover:bg-[#97091f]"
      >
      <span v-if="showForm" class="material-symbols-outlined text-sm">close</span>
      <span v-else class="material-symbols-outlined text-sm">upload_file</span>
        {{ showForm ? 'Annuler' : 'Ajouter un document' }}
      </button>
    </div>

    <div v-if="errorMessage" class="p-3 bg-red-50 text-red-700 text-xs rounded border border-red-200">
      {{ errorMessage }}
    </div>

    <div v-if="showForm" class="bg-red-50 p-4 rounded-xl border border-red-100 shadow-inner max-w-lg">
      <form @submit.prevent="handleSubmit" class="space-y-3 text-sm">
        
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Fichier</label>
          <input 
            type="file" 
            ref="fileInput"
            @change="handleFileChange"
            required
            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-[#d10f2f] file:text-white hover:file:bg-[#97091f] cursor-pointer bg-white border border-red-200 rounded-lg"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Catégorie</label>
            <select v-model="form.category" class="w-full border border-red-200 rounded-lg p-2 bg-white text-gray-700 focus:border-red-300 focus:ring-2 focus:ring-red-100 outline-none">
              <option value="Identité">Identité (CIN, Passeport)</option>
              <option value="Contrat">Contrat & Avenants</option>
              <option value="Social/Familial">Social (RIB, Sécurité Sociale)</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Numéro (obligatoire pour Identité)</label>
            <input type="text" v-model="form.numero" :required="form.category === 'Identité'" class="w-full border border-red-200 rounded-lg p-2 bg-white text-gray-700 focus:border-red-300 focus:ring-2 focus:ring-red-100 outline-none" placeholder="Ex: N° Passeport..." />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 uppercase mb-1">Date d'expiration (Opt.)</label>
            <input type="date" v-model="form.expiry_date" class="w-full border border-red-200 rounded-lg p-2 bg-white text-gray-700 focus:border-red-300 focus:ring-2 focus:ring-red-100 outline-none" />
          </div>
        </div>

        <button 
          type="submit" 
          :disabled="uploading"
          class="w-full bg-[#d10f2f] hover:bg-[#97091f] disabled:bg-red-300 text-white font-medium py-2 rounded-lg transition-colors flex justify-center items-center gap-2"
        >
          <span v-if="uploading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
          {{ uploading ? 'Envoi en cours...' : 'Envoyer le document' }}
        </button>
      </form>
    </div>

    <div v-if="loading" class="text-center py-4 text-sm text-gray-400">Chargement des documents...</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div v-if="documents.length === 0" class="col-span-full py-6 text-center text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-xl">
        Aucun document enregistré pour cet employé.
      </div>
      
      <div 
        v-for="doc in documents" 
        :key="doc.id"
        class="flex items-center justify-between p-3 bg-white border border-red-100 rounded-xl shadow-sm hover:shadow transition-shadow"
      >
        <button
          type="button"
          @click="handleDownload(doc)"
          class="flex items-center gap-3 overflow-hidden flex-1 text-left min-w-0 rounded-lg hover:bg-red-50/60 transition-colors p-1 -m-1"
          :disabled="downloadingDocumentId === doc.id"
          :title="`Télécharger ${doc.file_name}`"
        >
          <div class="p-2 bg-red-50 text-[#d10f2f] rounded-lg shrink-0 flex items-center justify-center">
            <span class="material-symbols-outlined text-xl">{{ getCategoryIcon(doc.category) }}</span>
          </div>
          <div class="overflow-hidden min-w-0">
            <p class="text-sm font-semibold text-gray-900 truncate" :title="doc.file_name">{{ doc.file_name }}</p>
            <div class="flex items-center gap-2 text-[10px] text-gray-500 font-medium uppercase mt-0.5">
              <span>{{ doc.category }}</span>
              <span v-if="doc.numero" class="text-gray-700 font-bold border-l pl-2 border-gray-300">
                N°: {{ doc.numero }}
              </span>
              <span v-if="doc.expiry_date" class="text-orange-500">
                • Exp: {{ doc.expiry_date }}
              </span>
            </div>
          </div>
        </button>
        
        <div class="flex items-center gap-1 shrink-0 ml-2">
          <button
            type="button"
            @click="handleDownload(doc)"
            class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            :disabled="downloadingDocumentId === doc.id"
            title="Télécharger"
          >
            <span class="material-symbols-outlined text-sm">download</span>
          </button>
          <button @click="handleDelete(doc.id)" class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors" title="Supprimer">
            <span class="material-symbols-outlined text-sm">delete</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>