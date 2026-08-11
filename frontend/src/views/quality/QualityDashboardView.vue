<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import AppLayout from "@/layouts/AppLayout.vue";
import { qualityService, type QualityDocument } from "@/services/quality";
import { useToast } from "@/composables/useToast";
import QualityDocumentCreateModal from "./QualityDocumentCreateModal.vue";
import { getStoredProfile } from "@/services/session";

const router = useRouter();
const toast = useToast();
const profile = getStoredProfile();

const documents = ref<QualityDocument[]>([]);
const loading = ref(true);
const activeTab = ref("ALL"); 
const showCreateModal = ref(false);

const canCreate = computed(() => {
  return profile?.roles?.some(r => r === "Qualité" || r === "Admin" || r === "Direction");
});

const loadDocuments = async () => {
  loading.value = true;
  try {
    documents.value = await qualityService.getDocuments(activeTab.value === "PENDING_ME");
  } catch (error) {
    toast.error("Erreur lors du chargement des documents");
  } finally {
    loading.value = false;
  }
};

const openDocument = (doc: QualityDocument) => {
  router.push(`/quality/${doc.id}`);
};

const handleDocumentCreated = () => {
  showCreateModal.value = false;
  loadDocuments();
};

onMounted(() => {
  loadDocuments();
});

const getStatusBadge = (status: string) => {
  switch (status) {
    case "IN_REVIEW":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "APPROVED":
      return "bg-green-100 text-green-800 border-green-200";
    case "REJECTED":
      return "bg-red-100 text-red-800 border-red-200";
    case "PUBLISHED":
      return "bg-blue-100 text-blue-800 border-blue-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
};
</script>

<template>
  <AppLayout>
    <div class="h-full flex flex-col bg-gray-50/50">
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 px-8 py-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Gestion Documentaire Qualité</h1>
            <p class="text-sm text-gray-500 mt-1">Gérez le cycle de vie de vos documents qualité</p>
          </div>
          <button
            v-if="canCreate"
            @click="showCreateModal = true"
            class="flex items-center gap-2 bg-[#d10f2f] hover:bg-[#a80c26] text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            <span class="material-symbols-outlined text-sm">add</span>
            Nouveau Document
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex items-center gap-6 mt-8 border-b border-gray-200">
          <button
            @click="activeTab = 'ALL'; loadDocuments()"
            class="pb-4 text-sm font-medium transition-colors relative"
            :class="activeTab === 'ALL' ? 'text-[#d10f2f]' : 'text-gray-500 hover:text-gray-700'"
          >
            Tous les documents
            <div v-if="activeTab === 'ALL'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-[#d10f2f] rounded-t-full"></div>
          </button>
          <button
            @click="activeTab = 'PENDING_ME'; loadDocuments()"
            class="pb-4 text-sm font-medium transition-colors relative"
            :class="activeTab === 'PENDING_ME' ? 'text-[#d10f2f]' : 'text-gray-500 hover:text-gray-700'"
          >
            Mes validations en attente
            <div v-if="activeTab === 'PENDING_ME'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-[#d10f2f] rounded-t-full"></div>
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-auto p-8">
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d10f2f]"></div>
        </div>
        
        <div v-else-if="documents.length === 0" class="flex flex-col items-center justify-center h-64 bg-white rounded-xl border border-gray-200 border-dashed">
          <div class="h-12 w-12 rounded-full bg-red-50 flex items-center justify-center mb-4">
            <span class="material-symbols-outlined text-red-600">inventory_2</span>
          </div>
          <h3 class="text-sm font-medium text-gray-900">Aucun document trouvé</h3>
          <p class="text-xs text-gray-500 mt-1">
            {{ activeTab === 'PENDING_ME' ? "Vous n'avez aucun document en attente de validation." : "Aucun document qualité n'a été créé." }}
          </p>
        </div>

        <div v-else class="grid gap-4">
          <div
            v-for="doc in documents"
            :key="doc.id"
            @click="openDocument(doc)"
            class="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-all cursor-pointer flex items-center justify-between group"
          >
            <div class="flex items-center gap-4">
              <div class="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-500 group-hover:bg-red-50 group-hover:text-[#d10f2f] transition-colors">
                <span class="material-symbols-outlined">description</span>
              </div>
              <div>
                <h3 class="font-medium text-gray-900">{{ doc.title }}</h3>
                <div class="flex items-center gap-3 text-xs text-gray-500 mt-1">
                  <span class="flex items-center gap-1">
                    <span class="material-symbols-outlined" style="font-size: 14px;">calendar_today</span>
                    {{ new Date(doc.created_at).toLocaleDateString('fr-FR') }}
                  </span>
                  <span>•</span>
                  <span>Version {{ doc.versions.length }}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-4">
              <span 
                class="px-2.5 py-1 text-xs font-medium rounded-full border"
                :class="getStatusBadge(doc.status)"
              >
                {{ doc.status }}
              </span>
              <span class="material-symbols-outlined text-gray-400 group-hover:text-gray-600 transition-colors">
                chevron_right
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <QualityDocumentCreateModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="handleDocumentCreated"
    />
  </AppLayout>
</template>
