<template>
  <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden transform transition-all">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-bold text-gray-900">
          {{ isEdit ? 'Modifier Rôle' : 'Nouveau Rôle' }}
        </h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 overflow-y-auto flex-1">
        <div class="space-y-6">
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Nom du rôle</label>
              <input 
                v-model="formData.name"
                type="text" 
                required
                :disabled="isEdit && formData.name === 'Admin'"
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition disabled:opacity-50"
              />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea 
                v-model="formData.description"
                rows="2"
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              ></textarea>
            </div>
          </div>

          <div>
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Permissions</h4>
            
            <div v-if="loadingPermissions" class="text-sm text-gray-500 py-4 text-center">
              Chargement des permissions...
            </div>
            
            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div v-for="(perms, category) in groupedPermissions" :key="category" class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                <h5 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-2 border-b border-gray-200">{{ category }}</h5>
                <div class="space-y-2">
                  <label 
                    v-for="perm in perms" 
                    :key="perm.code"
                    class="flex items-start gap-3 cursor-pointer group"
                  >
                    <div class="flex items-center h-5">
                      <input 
                        type="checkbox" 
                        :value="perm.code"
                        v-model="formData.permission_codes"
                        class="w-4 h-4 text-blue-600 bg-white border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                      />
                    </div>
                    <div class="flex flex-col">
                      <span class="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition">{{ perm.name }}</span>
                      <span class="text-xs text-gray-500">{{ perm.description }}</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="error" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {{ error }}
        </div>
      </form>
      
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3 bg-gray-50/50">
        <button 
          type="button"
          @click="$emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 border border-gray-200 rounded-lg transition"
        >
          Annuler
        </button>
        <button 
          @click="handleSubmit"
          :disabled="loading"
          class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition shadow-sm disabled:opacity-50"
        >
          {{ loading ? 'Enregistrement...' : (isEdit ? 'Mettre à jour' : 'Créer') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { roleService, type Role, type Permission } from '@/services/roleService';

const props = defineProps<{
  role?: Role | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const isEdit = computed(() => !!props.role);
const loading = ref(false);
const loadingPermissions = ref(true);
const error = ref('');
const permissions = ref<Permission[]>([]);

const formData = ref({
  name: '',
  description: '',
  permission_codes: [] as string[]
});

const groupedPermissions = computed(() => {
  const groups: Record<string, Permission[]> = {};
  
  permissions.value.forEach(p => {
    // Determine category based on prefix (e.g. "employees.read" -> "employees")
    const prefix = p.code.split('.')[0];
    const categoryName = {
      'employees': 'Employés',
      'users': 'Utilisateurs',
      'roles': 'Rôles',
      'notifications': 'Notifications',
      'hr': 'Planning RH',
      'contracts': 'Contrats',
      'documents': 'Documents',
      'stock': 'Stock',
      'dashboard': 'Tableau de bord',
      'projects': 'Projets',
      'tasks': 'Tâches',
      'fuel_requests': 'Carburant',
      'requests': 'Demandes Générales'
    }[prefix] || prefix.toUpperCase();

    if (!groups[categoryName]) {
      groups[categoryName] = [];
    }
    groups[categoryName].push(p);
  });
  
  return groups;
});

onMounted(async () => {
  loadingPermissions.value = true;
  try {
    permissions.value = await roleService.getPermissions();
  } catch (err) {
    console.error('Erreur de chargement des permissions', err);
    error.value = "Impossible de charger les permissions.";
  } finally {
    loadingPermissions.value = false;
  }

  if (props.role) {
    formData.value = {
      name: props.role.name,
      description: props.role.description || '',
      permission_codes: props.role.permissions.map(p => p.code)
    };
  }
});

const handleSubmit = async () => {
  if (!formData.value.name.trim()) {
    error.value = "Le nom du rôle est requis.";
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    if (isEdit.value && props.role) {
      await roleService.updateRole(props.role.id, formData.value);
    } else {
      await roleService.createRole(formData.value);
    }
    emit('saved');
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Une erreur est survenue lors de l'enregistrement.";
  } finally {
    loading.value = false;
  }
};
</script>
