<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { getNorms, createNorm, uploadNormVersion, getNormHistory, getCategories, deleteNorm, type Norm, type NormVersion, type NormCategory } from "@/services/norms";
import AppLayout from '@/layouts/AppLayout.vue';

const norms = ref<Norm[]>([]);
const categories = ref<NormCategory[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// Filters
const searchQuery = ref("");
const selectedCategoryId = ref<number | ''>('');
const dateFrom = ref("");
const dateTo = ref("");

// Modal states
const showCreateModal = ref(false);
const showUploadModal = ref(false);
const showHistoryModal = ref(false);
const showPreviewModal = ref(false);

const selectedNorm = ref<Norm | null>(null);
const normHistory = ref<NormVersion[]>([]);
const previewUrl = ref("");
const previewTitle = ref("");

// Form models
const newNorm = ref({ code: "", title: "", category_id: 1, file: null as File | null });
const uploadData = ref({ version_number: 1, file: null as File | null });

const fetchData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const [fetchedCategories, fetchedNorms] = await Promise.all([
      getCategories(),
      getNorms()
    ]);
    categories.value = fetchedCategories;
    norms.value = fetchedNorms;
    if (categories.value.length > 0 && newNorm.value.category_id === 1) {
      newNorm.value.category_id = categories.value[0].id;
    }
  } catch (err: any) {
    error.value = "Erreur lors du chargement des normes";
    console.error(err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});

const activeVersion = (norm: Norm) => {
  return norm.versions?.find((v) => v.is_active);
};

const getCategoryName = (categoryId: number) => {
  return categories.value.find(c => c.id === categoryId)?.name || 'Inconnue';
};

const filteredNorms = computed(() => {
  return norms.value.filter((n) => {
    // 1. Search (code or title)
    const q = searchQuery.value.toLowerCase();
    const matchesSearch = !q || n.title.toLowerCase().includes(q) || n.code.toLowerCase().includes(q);
    
    // 2. Category
    const matchesCategory = selectedCategoryId.value === '' || n.category_id === selectedCategoryId.value;
    
    // 3. Dates (using active version date)
    const activeV = activeVersion(n);
    let matchesDate = true;
    if (activeV && (dateFrom.value || dateTo.value)) {
      const vDate = new Date(activeV.created_at);
      if (dateFrom.value) {
        matchesDate = matchesDate && vDate >= new Date(dateFrom.value);
      }
      if (dateTo.value) {
        const to = new Date(dateTo.value);
        to.setHours(23, 59, 59, 999);
        matchesDate = matchesDate && vDate <= to;
      }
    }

    return matchesSearch && matchesCategory && matchesDate;
  });
});

const handleCreateNorm = async () => {
  if (!newNorm.value.file || !newNorm.value.code || !newNorm.value.title) {
    alert("Veuillez remplir tous les champs et joindre un fichier.");
    return;
  }
  try {
    await createNorm({
      code: newNorm.value.code,
      title: newNorm.value.title,
      category_id: newNorm.value.category_id,
      file: newNorm.value.file
    });
    showCreateModal.value = false;
    newNorm.value = { code: "", title: "", category_id: categories.value[0]?.id || 1, file: null };
    await fetchData();
  } catch (err: any) {
    alert("Erreur de création");
  }
};

const handleNewNormFile = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    newNorm.value.file = target.files[0];
  }
};

const openUploadModal = (norm: Norm) => {
  selectedNorm.value = norm;
  const currentActive = activeVersion(norm);
  uploadData.value.version_number = currentActive ? currentActive.version_number + 1 : 1;
  uploadData.value.file = null;
  showUploadModal.value = true;
};

const handleUpload = async () => {
  if (!selectedNorm.value || !uploadData.value.file) return;
  try {
    await uploadNormVersion(selectedNorm.value.id, uploadData.value.version_number, uploadData.value.file);
    showUploadModal.value = false;
    await fetchData();
  } catch (err: any) {
    alert("Erreur lors de l'upload");
  }
};

const handleDeleteNorm = async (id: number) => {
  if (!confirm("Êtes-vous sûr de vouloir supprimer cette norme ? Cette action est irréversible et supprimera également toutes ses versions.")) return;
  try {
    await deleteNorm(id);
    await fetchData();
  } catch (err) {
    alert("Erreur lors de la suppression de la norme");
  }
};

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    uploadData.value.file = target.files[0];
  }
};

const viewHistory = async (norm: Norm) => {
  selectedNorm.value = norm;
  try {
    normHistory.value = await getNormHistory(norm.id);
    showHistoryModal.value = true;
  } catch (err) {
    alert("Erreur lors du chargement de l'historique");
  }
};

const getBaseUrl = () => {
  const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (configuredBaseUrl) return configuredBaseUrl.replace(/\/+$/, "");
  return "http://localhost:8000";
};

const getFileUrl = (path: string) => {
  if (path.startsWith("http")) return path;
  return `${getBaseUrl()}/${path}`;
};

const previewIsUnsupported = ref(false);

const openPreview = (norm: Norm) => {
  const activeV = activeVersion(norm);
  if (activeV) {
    const url = getFileUrl(activeV.file_url);
    previewUrl.value = url;
    previewTitle.value = `${norm.code} - ${norm.title}`;
    
    const ext = url.split('.').pop()?.toLowerCase();
    const unsupported = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'csv'];
    previewIsUnsupported.value = unsupported.includes(ext || '');
    
    showPreviewModal.value = true;
  }
};

const downloadFile = (url: string, filename: string) => {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.target = '_blank';
  document.body.appendChild(a);
  a.click();
  a.remove();
};
</script>

<template>
  <AppLayout>
    <div class="min-h-screen bg-gray-50/50 p-8">
      <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header Section -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 shadow-sm border border-gray-100 rounded-2xl">
          <div>
            <h1 class="text-3xl font-bold bg-gradient-to-r from-red-600 to-red-800 bg-clip-text text-transparent">
              Bibliothèque de Normes
            </h1>
            <p class="text-gray-500 mt-1">Consultez, lisez et gérez vos documents normatifs sous forme de tableau.</p>
          </div>
          <button 
            @click="showCreateModal = true"
            class="flex items-center gap-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white px-5 py-2.5 rounded-xl font-medium shadow-md shadow-red-200 transition-all transform hover:-translate-y-0.5"
          >
            <span class="material-symbols-outlined text-sm">add</span>
            Nouvelle Norme
          </button>
        </div>

        <!-- Filters Section -->
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="relative md:col-span-1">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Recherche</label>
            <span class="material-symbols-outlined absolute left-3 top-[34px] text-gray-400">search</span>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Code ou Titre..." 
              class="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all"
            />
          </div>
          
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Catégorie</label>
            <select v-model="selectedCategoryId" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 outline-none">
              <option value="">Toutes les catégories</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
          
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Modifié après</label>
            <input v-model="dateFrom" type="date" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Modifié avant</label>
            <input v-model="dateTo" type="date" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 outline-none" />
          </div>
        </div>

        <!-- Data Table -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div v-if="loading" class="flex justify-center items-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
          </div>
          
          <div v-else-if="error" class="m-8 bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-center gap-3">
            <span class="material-symbols-outlined">error</span>
            {{ error }}
          </div>
          
          <div v-else class="overflow-x-auto">
            <table class="w-full whitespace-nowrap text-left border-collapse">
              <thead>
                <tr class="bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th class="px-6 py-4">Code</th>
                  <th class="px-6 py-4">Titre de la Norme</th>
                  <th class="px-6 py-4">Catégorie</th>
                  <th class="px-6 py-4">Version</th>
                  <th class="px-6 py-4">Date de MAJ</th>
                  <th class="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="norm in filteredNorms" :key="norm.id" class="hover:bg-gray-50/50 transition-colors group">
                  <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-red-50 text-red-700 border border-red-100">
                      {{ norm.code }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <p class="text-sm font-semibold text-gray-900 truncate max-w-xs" :title="norm.title">{{ norm.title }}</p>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-sm text-gray-600">{{ getCategoryName(norm.category_id) }}</span>
                  </td>
                  <td class="px-6 py-4">
                    <div v-if="activeVersion(norm)" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
                      v{{ activeVersion(norm)?.version_number }}
                    </div>
                    <span v-else class="text-xs text-amber-500">Aucune</span>
                  </td>
                  <td class="px-6 py-4">
                    <span v-if="activeVersion(norm)" class="text-sm text-gray-500">
                      {{ new Date(activeVersion(norm)!.created_at).toLocaleDateString('fr-FR') }}
                    </span>
                    <span v-else class="text-gray-400">-</span>
                  </td>
                  <td class="px-6 py-4 text-right flex items-center justify-end gap-2">
                    
                    <button 
                      v-if="activeVersion(norm)"
                      @click="openPreview(norm)"
                      class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                      title="Prévisualiser"
                    >
                      <span class="material-symbols-outlined text-[20px]">visibility</span>
                    </button>

                    <button 
                      v-if="activeVersion(norm)"
                      @click="downloadFile(getFileUrl(activeVersion(norm)!.file_url), activeVersion(norm)!.file_url.split('/').pop() || 'document')"
                      class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition"
                      title="Télécharger"
                    >
                      <span class="material-symbols-outlined text-[20px]">download</span>
                    </button>

                    <button 
                      @click="openUploadModal(norm)"
                      class="p-2 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition"
                      title="Nouvelle version"
                    >
                      <span class="material-symbols-outlined text-[20px]">upload_file</span>
                    </button>

                    <button 
                      @click="viewHistory(norm)"
                      class="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition"
                      title="Historique"
                    >
                      <span class="material-symbols-outlined text-[20px]">history</span>
                    </button>

                    <button 
                      @click="handleDeleteNorm(norm.id)"
                      class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                      title="Supprimer"
                    >
                      <span class="material-symbols-outlined text-[20px]">delete</span>
                    </button>

                  </td>
                </tr>
                <tr v-if="filteredNorms.length === 0">
                  <td colspan="6" class="px-6 py-12 text-center text-gray-500">
                    Aucune norme ne correspond à vos critères.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- Modals -->
      
      <!-- Preview Modal -->
      <div v-if="showPreviewModal" class="fixed inset-0 z-50 flex items-center justify-center p-6 md:p-12">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-gray-900/80 backdrop-blur-sm" @click="showPreviewModal = false"></div>
        
        <!-- Modal Content -->
        <div class="relative w-full h-full max-w-6xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col z-10">
          <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50 flex-shrink-0">
            <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <span class="material-symbols-outlined text-red-600">description</span>
              {{ previewTitle }}
            </h3>
            <div class="flex items-center gap-2">
              <button @click="downloadFile(previewUrl, previewTitle)" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200 rounded-lg transition flex items-center gap-1">
                <span class="material-symbols-outlined text-[18px]">download</span> Télécharger
              </button>
              <button @click="showPreviewModal = false" class="p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-900 rounded-lg transition">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
          </div>
          <div class="flex-1 bg-gray-100 relative">
            <template v-if="previewIsUnsupported">
              <div class="absolute inset-0 flex flex-col items-center justify-center p-4">
                <div class="text-center p-8 bg-white rounded-xl shadow-sm border border-gray-200 max-w-lg w-full">
                  <span class="material-symbols-outlined text-gray-400 text-5xl mb-4">description</span>
                  <h4 class="text-lg font-medium text-gray-900 mb-2">Aperçu non disponible</h4>
                  <p class="text-sm text-gray-500 mb-6">Les fichiers Microsoft Office (Word, Excel...) ne peuvent pas être lus directement dans le navigateur.</p>
                  <button @click="downloadFile(previewUrl, previewTitle)" class="px-5 py-2.5 bg-red-600 text-white font-medium hover:bg-red-700 rounded-xl transition shadow-sm shadow-red-200 flex items-center justify-center gap-2 mx-auto">
                    <span class="material-symbols-outlined text-[20px]">download</span>
                    Télécharger le fichier
                  </button>
                </div>
              </div>
            </template>
            <iframe v-else :src="previewUrl" class="absolute inset-0 w-full h-full border-0"></iframe>
          </div>
        </div>
      </div>

      <!-- Create Norm Modal -->
      <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm">
        <div class="bg-white rounded-2xl w-full max-w-md shadow-xl overflow-hidden">
          <div class="p-6 border-b border-gray-100 flex justify-between items-center">
            <h3 class="text-xl font-semibold text-gray-900">Nouvelle Norme</h3>
            <button @click="showCreateModal = false" class="text-gray-400 hover:text-gray-600">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Code (ex: ISO-9001)</label>
              <input v-model="newNorm.code" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-red-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Titre</label>
              <input v-model="newNorm.title" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-red-500 outline-none" />
            </div>
            <div>
               <label class="block text-sm font-medium text-gray-700 mb-1">Catégorie</label>
               <select v-model.number="newNorm.category_id" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-red-500 outline-none bg-white">
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
               </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Fichier initial (PDF, Doc...)</label>
              <div class="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:bg-gray-50 transition relative">
                <input type="file" @change="handleNewNormFile" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                <div class="flex flex-col items-center">
                  <span class="material-symbols-outlined text-gray-400 text-3xl mb-2">cloud_upload</span>
                  <span class="text-sm font-medium text-gray-700">{{ newNorm.file ? newNorm.file.name : "Cliquez ou glissez un fichier ici" }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="p-6 bg-gray-50 flex justify-end gap-3">
            <button @click="showCreateModal = false" class="px-5 py-2.5 text-gray-600 font-medium hover:bg-gray-100 rounded-xl transition">Annuler</button>
            <button @click="handleCreateNorm" class="px-5 py-2.5 bg-red-600 text-white font-medium hover:bg-red-700 rounded-xl transition shadow-sm shadow-red-200">Créer</button>
          </div>
        </div>
      </div>

      <!-- Upload Version Modal -->
      <div v-if="showUploadModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm">
        <div class="bg-white rounded-2xl w-full max-w-md shadow-xl overflow-hidden">
          <div class="p-6 border-b border-gray-100 flex justify-between items-center">
            <h3 class="text-xl font-semibold text-gray-900">Nouvelle version</h3>
            <button @click="showUploadModal = false" class="text-gray-400 hover:text-gray-600">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="p-6 space-y-5">
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
               <p class="font-medium text-gray-900">{{ selectedNorm?.code }}</p>
               <p class="text-sm text-gray-500 mt-1">{{ selectedNorm?.title }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Numéro de version</label>
              <input v-model.number="uploadData.version_number" type="number" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-red-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Fichier (PDF, Doc...)</label>
              <div class="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:bg-gray-50 transition relative">
                <input type="file" @change="handleFileChange" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                <div class="flex flex-col items-center">
                  <span class="material-symbols-outlined text-gray-400 text-3xl mb-2">cloud_upload</span>
                  <span class="text-sm font-medium text-gray-700">{{ uploadData.file ? uploadData.file.name : "Cliquez ou glissez un fichier ici" }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="p-6 bg-gray-50 flex justify-end gap-3">
            <button @click="showUploadModal = false" class="px-5 py-2.5 text-gray-600 font-medium hover:bg-gray-100 rounded-xl transition">Annuler</button>
            <button @click="handleUpload" :disabled="!uploadData.file" class="px-5 py-2.5 bg-red-600 text-white font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition shadow-sm shadow-red-200">Uploader</button>
          </div>
        </div>
      </div>

      <!-- History Modal -->
      <div v-if="showHistoryModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm">
        <div class="bg-white rounded-2xl w-full max-w-2xl shadow-xl overflow-hidden max-h-[90vh] flex flex-col">
          <div class="p-6 border-b border-gray-100 flex justify-between items-center">
            <div>
              <h3 class="text-xl font-semibold text-gray-900">Historique des versions</h3>
              <p class="text-sm text-gray-500 mt-1">{{ selectedNorm?.code }} - {{ selectedNorm?.title }}</p>
            </div>
            <button @click="showHistoryModal = false" class="text-gray-400 hover:text-gray-600">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="p-6 overflow-y-auto">
            <div v-if="normHistory.length === 0" class="text-center text-gray-500 py-8">
              Aucun historique disponible.
            </div>
            <div v-else class="relative border-l-2 border-gray-100 ml-4 space-y-8">
              <div v-for="version in normHistory" :key="version.id" class="relative pl-6">
                <!-- Timeline dot -->
                <span class="absolute -left-[9px] top-1 w-4 h-4 rounded-full border-4 border-white" :class="version.is_active ? 'bg-emerald-500' : 'bg-gray-300'"></span>
                
                <div class="flex items-start justify-between">
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                      <h4 class="font-bold text-gray-900">Version {{ version.version_number }}</h4>
                      <span v-if="version.is_active" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 uppercase tracking-wide">Active</span>
                    </div>
                    <p class="text-sm text-gray-500">{{ new Date(version.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute:'2-digit' }) }}</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button @click="downloadFile(getFileUrl(version.file_url), version.file_url.split('/').pop() || 'document')" class="p-2 text-gray-400 hover:text-green-600 rounded-lg transition" title="Télécharger">
                      <span class="material-symbols-outlined text-[18px]">download</span>
                    </button>
                    <a :href="getFileUrl(version.file_url)" target="_blank" class="p-2 text-gray-400 hover:text-blue-600 rounded-lg transition" title="Ouvrir dans un nouvel onglet">
                      <span class="material-symbols-outlined text-[18px]">open_in_new</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </AppLayout>
</template>
