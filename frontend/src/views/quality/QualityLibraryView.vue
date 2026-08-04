<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import AppLayout from "@/layouts/AppLayout.vue";
import { qualityService, type QualityDocument } from "@/services/quality";
import { useToast } from "@/composables/useToast";
import api from "@/services/api";

const downloadFile = (url: string, filename: string) => {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

const router = useRouter();
const toast = useToast();

const documents = ref<QualityDocument[]>([]);
const loading = ref(true);
const searchQuery = ref("");

const loadDocuments = async () => {
  loading.value = true;
  try {
    documents.value = await qualityService.getLibraryDocuments();
  } catch (error) {
    toast.error("Erreur lors du chargement de la bibliothèque");
  } finally {
    loading.value = false;
  }
};

const filteredDocuments = computed(() => {
  if (!searchQuery.value.trim()) return documents.value;
  const q = searchQuery.value.toLowerCase();
  return documents.value.filter(doc => doc.title.toLowerCase().includes(q));
});

const openDocument = (doc: QualityDocument) => {
  router.push(`/quality/${doc.id}`);
};

const downloadLatestVersion = async (doc: QualityDocument, event: Event) => {
  event.stopPropagation();
  if (!doc.versions || doc.versions.length === 0) return;
  const latestVersion = doc.versions[0];
  try {
    const response = await api.get(`/quality/documents/${doc.id}/download/${latestVersion.id}`);
    const url = response.data.url;
    downloadFile(url, latestVersion.original_filename);
  } catch (error: any) {
    toast.error("Erreur lors du téléchargement");
  }
};

onMounted(() => {
  loadDocuments();
});
</script>

<template>
  <AppLayout>
    <div class="h-full flex flex-col bg-gray-50/50">
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 px-8 py-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span class="material-symbols-outlined text-[#d10f2f]">local_library</span>
              Bibliothèque Qualité
            </h1>
            <p class="text-sm text-gray-500 mt-1">Consultez les documents qualité approuvés et accessibles pour vous</p>
          </div>
        </div>

        <!-- Search Bar -->
        <div class="mt-8 relative max-w-md">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">search</span>
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Rechercher un document par nom..."
            class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#d10f2f] focus:border-transparent text-sm"
          />
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-auto p-8">
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
        </div>
        
        <div v-else-if="filteredDocuments.length === 0" class="flex flex-col items-center justify-center h-64 bg-white rounded-xl border border-gray-200 border-dashed">
          <div class="h-12 w-12 rounded-full bg-red-50 flex items-center justify-center mb-4">
            <span class="material-symbols-outlined text-[#d10f2f]">menu_book</span>
          </div>
          <h3 class="text-sm font-medium text-gray-900">Aucun document trouvé</h3>
          <p class="text-xs text-gray-500 mt-1">
            {{ searchQuery ? "Aucun document ne correspond à votre recherche." : "La bibliothèque est actuellement vide pour votre profil." }}
          </p>
        </div>

        <div v-else class="grid gap-4">
          <div
            v-for="doc in filteredDocuments"
            :key="doc.id"
            @click="openDocument(doc)"
            class="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-all cursor-pointer flex items-center justify-between group"
          >
            <div class="flex items-center gap-4">
              <div class="h-10 w-10 rounded-lg bg-red-50 flex items-center justify-center text-[#d10f2f] transition-colors">
                <span class="material-symbols-outlined">menu_book</span>
              </div>
              <div>
                <h3 class="font-medium text-gray-900">{{ doc.title }}</h3>
                <div class="flex items-center gap-3 text-xs text-gray-500 mt-1">
                  <span class="flex items-center gap-1">
                    <span class="material-symbols-outlined" style="font-size: 14px;">calendar_today</span>
                    Mis à jour le {{ new Date(doc.updated_at).toLocaleDateString('fr-FR') }}
                  </span>
                  <span v-if="doc.versions && doc.versions.length > 0">•</span>
                  <span v-if="doc.versions && doc.versions.length > 0">Version {{ doc.versions[0].version_number }}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-4">
              <button
                v-if="doc.versions && doc.versions.length > 0"
                @click="(e) => downloadLatestVersion(doc, e)"
                class="flex items-center gap-1.5 text-xs font-medium text-[#d10f2f] hover:text-[#a80c26] hover:bg-red-50 px-3 py-1.5 rounded-md transition-colors border border-red-100 hover:border-red-200"
                title="Télécharger la dernière version"
              >
                <span class="material-symbols-outlined" style="font-size: 16px;">download</span>
                Télécharger
              </button>
              <span class="material-symbols-outlined text-gray-400 group-hover:text-gray-600 transition-colors ml-2">
                chevron_right
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
