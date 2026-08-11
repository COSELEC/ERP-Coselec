<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppLayout from "@/layouts/AppLayout.vue";
import { qualityService, type QualityDocument } from "@/services/quality";
import { useToast } from "@/composables/useToast";
import { getStoredProfile } from "@/services/session";

const route = useRoute();
const router = useRouter();
const toast = useToast();
const profile = getStoredProfile();

const doc = ref<QualityDocument | null>(null);
const loading = ref(true);

const fileInput = ref<HTMLInputElement | null>(null);
const uploadLoading = ref(false);

const reviewModalOpen = ref(false);
const reviewRole = ref<number | null>(null);
const reviewStatus = ref<"APPROVED" | "REJECTED">("APPROVED");
const reviewComment = ref("");
const reviewLoading = ref(false);

const availableRoles = ref<{id: number, name: string}[]>([]);

const visibilityRoleIds = ref<number[]>([]);
const visibilityLoading = ref(false);

const loadDocument = async () => {
  loading.value = true;
  try {
    const id = parseInt(route.params.id as string);
    doc.value = await qualityService.getDocument(id);
    availableRoles.value = await qualityService.getAvailableRoles();
    if (doc.value.visible_roles) {
      visibilityRoleIds.value = doc.value.visible_roles.map((r: any) => r.id);
    }
  } catch (error) {
    toast.error("Document introuvable");
    router.push("/quality");
  } finally {
    loading.value = false;
  }
};

const saveVisibility = async () => {
  if (!doc.value) return;
  visibilityLoading.value = true;
  try {
    await qualityService.updateDocumentVisibility(doc.value.id, visibilityRoleIds.value);
    toast.success("Accès mis à jour avec succès");
    await loadDocument();
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Erreur lors de la mise à jour des accès");
  } finally {
    visibilityLoading.value = false;
  }
};

onMounted(() => {
  loadDocument();
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

const getReviewStatusBadge = (status: string) => {
  switch (status) {
    case "PENDING":
      return "bg-gray-100 text-gray-600";
    case "APPROVED":
      return "bg-green-100 text-green-700";
    case "REJECTED":
      return "bg-red-100 text-red-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
};

const sortedVersions = computed(() => {
  if (!doc.value) return [];
  return [...doc.value.versions].sort((a, b) => b.version_number - a.version_number);
});

const pendingRolesForMe = computed(() => {
  if (!doc.value || !profile?.roles) return [];
  
  const normalizeStr = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  
  const myRoleIds = availableRoles.value
    .filter(r => profile.roles.some(pr => normalizeStr(pr) === normalizeStr(r.name)))
    .map(r => Number(r.id));
  
  const myUserId = Number(profile.id);
  
  return doc.value.role_reviews.filter(r => {
    const assignedUserId = r.assigned_user_id ? Number(r.assigned_user_id) : null;
    const roleId = Number(r.role_id);
    
    return r.status === "PENDING" && (
      assignedUserId === myUserId || 
      (assignedUserId === null && myRoleIds.includes(roleId))
    );
  });
});

const canUploadNewVersion = computed(() => {
  if (!doc.value || !profile) return false;
  
  const isCreator = doc.value.created_by_id === profile.id;
  const isAdmin = profile.roles?.some(r => r === "Admin" || r === "Qualité" || r === "Qualite");
  
  const normalizeStr = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  
  const isReviewer = doc.value.role_reviews.some(r => {
    if (r.assigned_user_id === profile.id) return true;
    const hasRole = availableRoles.value.some(role => 
      role.id === r.role_id && 
      profile.roles.some(pr => normalizeStr(pr) === normalizeStr(role.name))
    );
    return hasRole;
  });

  return doc.value.status === "REJECTED" && (isCreator || isAdmin || isReviewer);
});

const openReviewModal = (reviewId: number) => {
  reviewRole.value = reviewId;
  reviewStatus.value = "APPROVED";
  reviewComment.value = "";
  reviewModalOpen.value = true;
};

const submitReview = async () => {
  if (!doc.value || !reviewRole.value) return;
  if (reviewStatus.value === "REJECTED" && !reviewComment.value.trim()) {
    toast.error("Un commentaire est obligatoire pour un rejet.");
    return;
  }
  
  reviewLoading.value = true;
  try {
    await qualityService.submitReview(
      doc.value.id,
      reviewRole.value,
      reviewStatus.value,
      reviewComment.value
    );
    toast.success("Avis enregistré avec succès");
    reviewModalOpen.value = false;
    await loadDocument();
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Erreur lors de la validation");
  } finally {
    reviewLoading.value = false;
  }
};

const triggerFileInput = () => {
  if (fileInput.value) fileInput.value.click();
};

const uploadNewVersion = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!target.files || target.files.length === 0 || !doc.value) return;
  
  const file = target.files[0];
  uploadLoading.value = true;
  
  try {
    await qualityService.uploadNewVersion(doc.value.id, file);
    toast.success("Nouvelle version téléchargée avec succès");
    await loadDocument();
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Erreur lors du téléchargement");
  } finally {
    uploadLoading.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
};

const downloadVersion = async (versionId: number) => {
  if (!doc.value) return;
  try {
    const url = await qualityService.getFileUrl(doc.value.id, versionId);
    window.open(url, '_blank');
  } catch (error) {
    toast.error("Impossible de télécharger le fichier");
  }
};
const getReviewerDisplayName = (review: any) => {
  if (review.assigned_user) return review.assigned_user.name;

  if (review.assigned_user_id) {
    for (const role of availableRoles.value) {
      const user = role.users?.find((u: any) => u.id === review.assigned_user_id);
      if (user) return user.name;
    }
    return `Utilisateur #${review.assigned_user_id}`; 
  }
  
  const role = availableRoles.value.find(r => r.id === review.role_id);
  return role ? role.name : `Rôle #${review.role_id}`;
};

const canDeleteDocument = computed(() => {
  if (!doc.value || !profile) return false;
  const isCreator = doc.value.created_by_id === profile.id;
  const isAdmin = profile.roles?.some(r => r === "Admin" || r === "Qualité");
  return isCreator || isAdmin;
});

const deleteDocument = async () => {
  if (!doc.value || !confirm("Êtes-vous sûr de vouloir supprimer ce document ? Cette action est irréversible et supprimera toutes les versions associées.")) return;
  
  loading.value = true;
  try {
    await qualityService.deleteDocument(doc.value.id);
    toast.success("Document supprimé avec succès");
    router.push("/quality");
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "Erreur lors de la suppression");
    loading.value = false;
  }
};
</script>

<template>
  <AppLayout>
    <div v-if="loading" class="h-full flex justify-center items-center">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-[#d10f2f]"></div>
    </div>
    
    <div v-else-if="doc" class="h-full flex flex-col bg-gray-50/50 overflow-hidden">
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 px-8 py-6 flex-shrink-0">
        <button @click="router.push('/quality')" class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 transition-colors mb-4">
          <span class="material-symbols-outlined" style="font-size: 16px;">arrow_back</span>
          Retour aux documents
        </button>
        
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold text-gray-900">{{ doc.title }}</h1>
              <span class="px-3 py-1 text-xs font-semibold rounded-full border" :class="getStatusBadge(doc.status)">
                {{ doc.status }}
              </span>
            </div>
            <p v-if="doc.description" class="text-gray-500 mt-2 text-sm max-w-3xl">{{ doc.description }}</p>
          </div>
          
          <div class="flex items-center gap-3">
            <button 
              v-if="canDeleteDocument"
              @click="deleteDocument"
              class="flex items-center gap-2 bg-red-100 hover:bg-red-200 text-red-800 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
              :disabled="loading || uploadLoading"
              title="Supprimer définitivement ce document"
            >
              <span class="material-symbols-outlined text-sm">delete</span>
              Supprimer
            </button>

            <div v-if="canUploadNewVersion">
              <input type="file" class="hidden" ref="fileInput" @change="uploadNewVersion" accept=".pdf,.doc,.docx,.xls,.xlsx" />
              <button 
                @click="triggerFileInput"
                class="flex items-center gap-2 bg-[#d10f2f] hover:bg-[#a80c26] text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
                :disabled="uploadLoading"
              >
                <span v-if="uploadLoading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
                <span v-else class="material-symbols-outlined text-sm">cloud_upload</span>
                Soumettre nouvelle version
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-auto p-8">
        <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <!-- Left Column (Validation & Reviews) -->
          <div class="lg:col-span-2 space-y-6">
            
            <!-- Actions Pending For Me -->
            <div v-if="pendingRolesForMe.length > 0" class="bg-white rounded-xl border border-amber-200 shadow-sm overflow-hidden">
              <div class="bg-amber-50 px-6 py-4 border-b border-amber-200 flex items-center gap-2 text-amber-800">
                <span class="material-symbols-outlined">info</span>
                <h3 class="font-bold">Votre validation est requise</h3>
              </div>
              <div class="p-6">
                <p class="text-sm text-gray-600 mb-4">Vous devez valider ce document en tant que :</p>
                <div class="flex flex-wrap gap-3">
                  <button
                    v-for="rev in pendingRolesForMe"
                    :key="rev.id"
                    @click="openReviewModal(rev.id)"
                    class="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Valider ({{ getReviewerDisplayName(rev) }})
                  </button>
                </div>
              </div>
            </div>

            <!-- Visibility Section (For APPROVED documents) -->
            <div v-if="doc.status === 'APPROVED' && (isCreator || isAdmin)" class="bg-white rounded-xl border border-red-200 shadow-sm overflow-hidden mb-6">
              <div class="bg-red-50 px-6 py-4 border-b border-red-200 flex items-center gap-2 text-red-800">
                <span class="material-symbols-outlined">visibility</span>
                <h3 class="font-bold">Visibilité dans la bibliothèque</h3>
              </div>
              <div class="p-6">
                <p class="text-sm text-gray-600 mb-4">Sélectionnez les rôles qui peuvent consulter ce document dans la bibliothèque :</p>
                <div class="flex flex-wrap gap-3 mb-4">
                  <label v-for="role in availableRoles" :key="role.id" class="flex items-center gap-2 text-sm text-gray-700 bg-gray-50 border border-gray-200 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
                    <input type="checkbox" :value="role.id" v-model="visibilityRoleIds" class="rounded border-gray-300 text-[#d10f2f] focus:ring-[#d10f2f]" />
                    {{ role.name }}
                  </label>
                </div>
                <button 
                  @click="saveVisibility"
                  class="bg-[#d10f2f] hover:bg-[#a80c26] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                  :disabled="visibilityLoading"
                >
                  <span v-if="visibilityLoading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
                  <span v-else class="material-symbols-outlined text-sm">save</span>
                  Enregistrer les accès
                </button>
              </div>
            </div>

            <!-- Reviews Table -->
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-100">
                <h3 class="font-bold text-gray-900">État des Validations</h3>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-gray-600">
                  <thead class="bg-gray-50/50 text-gray-500 text-xs uppercase font-medium border-b border-gray-100">
                    <tr>
                      <th class="px-6 py-3">Assigné à</th>
                      <th class="px-6 py-3">Statut</th>
                      <th class="px-6 py-3">Validé par</th>
                      <th class="px-6 py-3">Commentaire</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100">
                    <tr v-for="review in doc.role_reviews" :key="review.id" class="hover:bg-gray-50/30 transition-colors">
                      <td class="px-6 py-4 font-medium text-gray-900">{{ getReviewerDisplayName(review) }}</td>
                      <td class="px-6 py-4">
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="getReviewStatusBadge(review.status)">
                          {{ review.status }}
                        </span>
                      </td>
                      <td class="px-6 py-4 text-gray-500">
                        {{ review.reviewed_by ? review.reviewed_by.name : (review.reviewed_by_id ? `Utilisateur #${review.reviewed_by_id}` : '-') }}
                      </td>
                      <td class="px-6 py-4 text-gray-500 max-w-xs truncate" :title="review.comment || ''">
                        {{ review.comment || '-' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
          </div>

          <!-- Right Column (History) -->
          <div class="space-y-6">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-6">
              <h3 class="font-bold text-gray-900 mb-6 flex items-center gap-2">
                <span class="material-symbols-outlined text-gray-400">history</span>
                Historique des versions
              </h3>
              
              <div class="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
                
                <div v-for="(v, index) in sortedVersions" :key="v.id" class="relative flex items-start">
                  <div class="w-10 h-10 rounded-full border-4 border-white flex items-center justify-center shrink-0 z-10"
                       :class="index === 0 ? 'bg-red-100 text-[#d10f2f]' : 'bg-gray-100 text-gray-500'">
                    <span class="material-symbols-outlined text-sm">{{ index === 0 ? 'stars' : 'description' }}</span>
                  </div>
                  <div class="ml-4 p-4 bg-gray-50 rounded-lg border border-gray-100 flex-1 min-w-0">
                    <div class="flex flex-wrap justify-between items-start gap-3">
                      <div class="min-w-0 flex-1">
                        <h4 class="font-semibold text-gray-900 text-sm">Version {{ v.version_number }}</h4>
                        <p class="text-xs text-gray-500 mt-1">{{ new Date(v.uploaded_at).toLocaleString('fr-FR') }}</p>
                        <p v-if="v.uploaded_by" class="text-xs text-gray-500 mt-1">Soumis par : <span class="font-medium">{{ v.uploaded_by.name }}</span></p>
                      </div>
                      <button @click="downloadVersion(v.id)" class="flex items-center gap-1.5 text-xs font-medium text-gray-600 hover:text-[#d10f2f] hover:bg-red-50 px-3 py-1.5 rounded-md transition-colors border border-gray-200 hover:border-red-200 shrink-0" title="Télécharger">
                        <span class="material-symbols-outlined" style="font-size: 16px;">download</span>
                        Télécharger
                      </button>
                    </div>
                    <div class="mt-2 text-xs font-medium text-gray-500 truncate w-full" :title="v.original_filename">
                      {{ v.original_filename }}
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>

    <!-- Review Modal -->
    <div v-if="reviewModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
          <h2 class="text-xl font-bold text-gray-900">Soumettre votre avis</h2>
          <button @click="reviewModalOpen = false" class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <div class="p-6 space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Décision</label>
            <div class="flex gap-4">
              <label class="flex-1 cursor-pointer">
                <input type="radio" v-model="reviewStatus" value="APPROVED" class="peer sr-only" />
                <div class="p-4 border border-gray-200 rounded-lg peer-checked:border-green-500 peer-checked:bg-green-50 peer-checked:text-green-800 flex items-center gap-2 transition-all">
                  <span class="material-symbols-outlined">check_circle</span> Approuver
                </div>
              </label>
              <label class="flex-1 cursor-pointer">
                <input type="radio" v-model="reviewStatus" value="REJECTED" class="peer sr-only" />
                <div class="p-4 border border-gray-200 rounded-lg peer-checked:border-red-500 peer-checked:bg-red-50 peer-checked:text-red-800 flex items-center gap-2 transition-all">
                  <span class="material-symbols-outlined">cancel</span> Rejeter
                </div>
              </label>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Commentaire <span v-if="reviewStatus === 'REJECTED'" class="text-red-500">*</span>
            </label>
            <textarea 
              v-model="reviewComment"
              rows="3"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f] focus:border-[#d10f2f] outline-none transition-all resize-none"
              placeholder="Expliquez votre décision..."
            ></textarea>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end gap-3">
          <button @click="reviewModalOpen = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" :disabled="reviewLoading">
            Annuler
          </button>
          <button @click="submitReview" class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#d10f2f] rounded-lg hover:bg-[#a80c26] transition-colors disabled:opacity-50" :disabled="reviewLoading">
            <span v-if="reviewLoading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
            Soumettre
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
