<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
      <div class="px-6 py-4 bg-gray-900 text-white flex justify-between items-center shrink-0">
        <h2 class="text-xl font-bold flex items-center gap-2">
          <span class="material-symbols-outlined">manage_accounts</span>
          Gérer les accès
        </h2>
        <button @click="$emit('close')" class="hover:bg-white/20 p-1 rounded-full transition">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      
      <div class="px-6 py-4 border-b border-gray-100 bg-gray-50 shrink-0">
        <h3 class="font-bold text-gray-900">Processus : {{ processus.name }}</h3>
        <p class="text-xs text-gray-500 mt-1">
          Sélectionnez les rôles et/ou les utilisateurs spécifiques autorisés à modifier les valeurs des indicateurs de ce processus.
          La direction Qualité a accès par défaut.
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 flex-1 overflow-y-auto space-y-6">
        <!-- Rôles autorisés -->
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">Rôles Autorisés</label>
          <div class="bg-gray-50 border border-gray-200 rounded-xl p-3 max-h-48 overflow-y-auto space-y-2">
            <label v-for="role in availableRoles" :key="role.id" class="flex items-center gap-2 cursor-pointer p-1 hover:bg-gray-100 rounded">
              <input 
                type="checkbox" 
                :value="role.name" 
                v-model="selectedRoles"
                class="text-red-600 focus:ring-red-500 rounded"
              />
              <span class="text-sm text-gray-800 font-medium">{{ role.name }}</span>
            </label>
          </div>
        </div>

        <!-- Utilisateurs autorisés -->
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">Utilisateurs Spécifiques Autorisés</label>
          
          <div class="relative mb-3">
            <span class="material-symbols-outlined absolute left-3 top-2 text-gray-400 text-sm">search</span>
            <input 
              v-model="userSearch"
              type="text" 
              placeholder="Rechercher un utilisateur..."
              class="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
            />
          </div>

          <div class="bg-gray-50 border border-gray-200 rounded-xl p-3 max-h-48 overflow-y-auto space-y-2">
            <label v-for="user in filteredUsers" :key="user.id" class="flex items-center gap-3 cursor-pointer p-1.5 hover:bg-gray-100 rounded">
              <input 
                type="checkbox" 
                :value="user.id" 
                v-model="selectedUsers"
                class="text-red-600 focus:ring-red-500 rounded"
              />
              <div class="w-7 h-7 rounded-full bg-red-100 text-red-700 font-bold flex items-center justify-center text-xs shrink-0">
                {{ user.first_name[0] }}{{ user.last_name[0] }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-800 font-medium truncate">{{ user.first_name }} {{ user.last_name }}</div>
                <div class="text-[10px] text-gray-500 truncate">{{ user.title || 'Employé' }}</div>
              </div>
            </label>
            <div v-if="filteredUsers.length === 0" class="text-center text-gray-400 text-sm py-4">
              Aucun utilisateur trouvé.
            </div>
          </div>
        </div>

        <div class="mt-8 flex justify-end gap-3 pt-4 border-t">
          <button 
            type="button" 
            @click="$emit('close')" 
            class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition font-semibold text-sm"
          >
            Annuler
          </button>
          <button 
            type="submit" 
            :disabled="loading"
            class="px-6 py-2 bg-gray-900 text-white hover:bg-black rounded-xl shadow-lg transition disabled:opacity-50 flex items-center gap-2 font-semibold text-sm"
          >
            <span v-if="loading" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
            Enregistrer
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { kpiService, type KPIProcessus } from '@/services/kpi';
import api from '@/services/api';
import { useToast } from '@/composables/useToast';

const props = defineProps<{
  processus: KPIProcessus;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const toast = useToast();
const loading = ref(false);

const availableRoles = ref<any[]>([]);
const availableUsers = ref<any[]>([]);
const userSearch = ref('');

const selectedRoles = ref<string[]>([]);
const selectedUsers = ref<number[]>([]);

onMounted(async () => {
  try {
    const [rolesRes, usersRes] = await Promise.all([
      api.get('/roles'),
      api.get('/users')
    ]);
    availableRoles.value = rolesRes.data;
    availableUsers.value = usersRes.data.filter((u: any) => u.is_active);
    
    selectedRoles.value = [...(props.processus.editor_role_names || [])];
    selectedUsers.value = [...(props.processus.editor_user_ids || [])];
  } catch (e) {
    console.error("Error fetching data for editors", e);
  }
});

const filteredUsers = computed(() => {
  if (!userSearch.value) return availableUsers.value;
  const q = userSearch.value.toLowerCase();
  return availableUsers.value.filter(u => 
    u.first_name.toLowerCase().includes(q) || 
    u.last_name.toLowerCase().includes(q)
  );
});

const handleSubmit = async () => {
  loading.value = true;
  try {
    await kpiService.configureEditors(props.processus.id, selectedRoles.value, selectedUsers.value);
    toast.success("Accès mis à jour avec succès");
    emit('saved');
  } catch (e: any) {
    const msg = e.response?.data?.detail || "Erreur lors de la mise à jour";
    toast.error(msg);
  } finally {
    loading.value = false;
  }
};
</script>
