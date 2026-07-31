<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { qualityService } from '@/services/quality';
import { useToast } from '@/composables/useToast';

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'created'): void;
}>();

const toast = useToast();

const title = ref('');
const description = ref('');
const file = ref<File | null>(null);
const loading = ref(false);

const availableRoles = ref<{id: number, name: string, users: {id: number, name: string}[]}[]>([]);

// Selection state
const selectedRoles = ref<number[]>([]);
const selectedUsersByRole = ref<Record<number, number[]>>({});

// UI state for expanding/collapsing roles in the tree
const expandedRoles = ref<number[]>([]);

onMounted(async () => {
  try {
    availableRoles.value = await qualityService.getAvailableRoles();
  } catch {
    toast.error("Erreur lors du chargement des rôles");
  }
});

const toggleRoleExpand = (roleId: number) => {
  if (expandedRoles.value.includes(roleId)) {
    expandedRoles.value = expandedRoles.value.filter(id => id !== roleId);
  } else {
    expandedRoles.value.push(roleId);
  }
};

const toggleRoleSelection = (roleId: number) => {
  if (selectedRoles.value.includes(roleId)) {
    // Deselect role and all its users
    selectedRoles.value = selectedRoles.value.filter(id => id !== roleId);
    selectedUsersByRole.value[roleId] = [];
  } else {
    // Select role (which implies any user can validate)
    selectedRoles.value.push(roleId);
    selectedUsersByRole.value[roleId] = []; // clear specific users
  }
};

const toggleUserSelection = (roleId: number, userId: number) => {
  if (selectedRoles.value.includes(roleId)) {
    // If the whole role was selected, deselect the role, and only select this user
    selectedRoles.value = selectedRoles.value.filter(id => id !== roleId);
    selectedUsersByRole.value[roleId] = [userId];
    return;
  }
  
  if (!selectedUsersByRole.value[roleId]) {
    selectedUsersByRole.value[roleId] = [];
  }
  
  if (selectedUsersByRole.value[roleId].includes(userId)) {
    selectedUsersByRole.value[roleId] = selectedUsersByRole.value[roleId].filter(id => id !== userId);
  } else {
    selectedUsersByRole.value[roleId].push(userId);
  }
};

const finalReviewers = computed(() => {
  const result: {role_id: number, user_id: number | null}[] = [];
  
  availableRoles.value.forEach(role => {
    if (selectedRoles.value.includes(role.id)) {
      result.push({ role_id: role.id, user_id: null });
    } else if (selectedUsersByRole.value[role.id]?.length > 0) {
      selectedUsersByRole.value[role.id].forEach(userId => {
        result.push({ role_id: role.id, user_id: userId });
      });
    }
  });
  
  return result;
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

const submit = async () => {
  if (!title.value.trim() || !file.value || finalReviewers.value.length === 0) {
    toast.error("Veuillez remplir tous les champs obligatoires (Titre, Fichier, Rôles)");
    return;
  }

  loading.value = true;
  try {
    await qualityService.createDocument(
      title.value.trim(),
      description.value.trim(),
      finalReviewers.value,
      file.value
    );
    toast.success("Document créé avec succès");
    emit('created');
  } catch (err: any) {
    toast.error(err.response?.data?.detail || "Erreur lors de la création");
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
        <h2 class="text-xl font-bold text-gray-900">Nouveau Document Qualité</h2>
        <button 
          @click="emit('close')"
          class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-colors"
        >
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 overflow-y-auto flex-1">
        <div class="space-y-6">
          
          <!-- Titre -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Titre du document <span class="text-red-500">*</span>
            </label>
            <input 
              v-model="title"
              type="text" 
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f] focus:border-[#d10f2f] outline-none transition-all"
              placeholder="Ex: Procédure de recrutement v1"
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Description (Optionnel)
            </label>
            <textarea 
              v-model="description"
              rows="3"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#d10f2f] focus:border-[#d10f2f] outline-none transition-all resize-none"
              placeholder="Brève description de l'objectif de ce document..."
            ></textarea>
          </div>

          <!-- Fichier -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Fichier (Brouillon initial) <span class="text-red-500">*</span>
            </label>
            
            <div 
              @dragover.prevent
              @drop="handleFileDrop"
              class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl hover:bg-gray-50 transition-colors relative"
              :class="{'border-[#d10f2f] bg-red-50/30': file}"
            >
              <div class="space-y-2 text-center">
                <span 
                  class="material-symbols-outlined text-4xl"
                  :class="file ? 'text-[#d10f2f]' : 'text-gray-400'"
                >
                  {{ file ? 'task' : 'cloud_upload' }}
                </span>
                
                <div class="flex text-sm text-gray-600 justify-center">
                  <label class="relative cursor-pointer rounded-md bg-transparent font-medium text-[#d10f2f] focus-within:outline-none hover:text-[#a80c26]">
                    <span>{{ file ? file.name : "Téléverser un fichier" }}</span>
                    <input type="file" class="sr-only" @change="handleFileSelect" accept=".pdf,.doc,.docx,.xls,.xlsx" />
                  </label>
                  <p class="pl-1" v-if="!file">ou glisser-déposer</p>
                </div>
                <p class="text-xs text-gray-500" v-if="!file">PDF, Word, Excel (Max 10MB)</p>
              </div>
            </div>
          </div>

          <!-- Rôles Requis -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Rôles ou Personnes devant valider le document <span class="text-red-500">*</span>
            </label>
            
            <div class="border border-gray-200 rounded-lg max-h-60 overflow-y-auto bg-white p-2">
              <div v-for="role in availableRoles" :key="role.id" class="mb-1">
                <!-- Role Row -->
                <div class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-lg transition-colors">
                  <button 
                    type="button"
                    @click="toggleRoleExpand(role.id)"
                    class="text-gray-400 hover:text-gray-600 p-0.5 rounded transition-colors"
                  >
                    <span class="material-symbols-outlined text-[20px]">
                      {{ expandedRoles.includes(role.id) ? 'expand_more' : 'chevron_right' }}
                    </span>
                  </button>
                  
                  <label class="flex items-center gap-2 cursor-pointer flex-1">
                    <input 
                      type="checkbox" 
                      :checked="selectedRoles.includes(role.id)"
                      @change="toggleRoleSelection(role.id)"
                      class="rounded border-gray-300 text-[#d10f2f] focus:ring-[#d10f2f] w-4 h-4 cursor-pointer"
                    />
                    <span class="font-medium text-sm text-gray-900 select-none">Rôle : {{ role.name }}</span>
                    <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full ml-auto">
                      {{ role.users.length }} employé(s)
                    </span>
                  </label>
                </div>
                
                <!-- Users under Role -->
                <div v-if="expandedRoles.includes(role.id)" class="pl-8 py-1 space-y-1">
                  <div v-if="role.users.length === 0" class="text-xs text-gray-400 italic px-2 py-1">
                    Aucun employé actif dans ce rôle
                  </div>
                  <label 
                    v-for="user in role.users" 
                    :key="user.id"
                    class="flex items-center gap-2 p-1.5 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                    :class="{'opacity-50': selectedRoles.includes(role.id)}"
                  >
                    <input 
                      type="checkbox" 
                      :checked="selectedRoles.includes(role.id) || (selectedUsersByRole[role.id] && selectedUsersByRole[role.id].includes(user.id))"
                      :disabled="selectedRoles.includes(role.id)"
                      @change="toggleUserSelection(role.id, user.id)"
                      class="rounded border-gray-300 text-amber-500 focus:ring-amber-500 w-4 h-4 cursor-pointer"
                    />
                    <span class="text-sm text-gray-600 select-none">{{ user.name }}</span>
                  </label>
                </div>
              </div>
            </div>
            
            <p v-if="finalReviewers.length === 0" class="text-xs text-red-500 mt-2">
              Vous devez sélectionner au moins un rôle ou une personne.
            </p>
          </div>

        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end gap-3">
        <button 
          @click="emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          :disabled="loading"
        >
          Annuler
        </button>
        <button 
          @click="submit"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#d10f2f] rounded-lg hover:bg-[#a80c26] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading || !title.trim() || !file || finalReviewers.length === 0"
        >
          <span v-if="loading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
          {{ loading ? 'Création...' : 'Créer et envoyer' }}
        </button>
      </div>
    </div>
  </div>
</template>
