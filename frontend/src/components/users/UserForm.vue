<template>
  <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden transform transition-all">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-bold text-gray-900">
          {{ isCreateAccountMode ? 'Créer un compte' : (isEdit ? 'Modifier Utilisateur' : 'Nouvel Utilisateur') }}
        </h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
              <input 
                v-model="formData.first_name"
                type="text" 
                required
                :readonly="isCreateAccountMode"
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                :class="{'opacity-70 cursor-not-allowed': isCreateAccountMode}"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
              <input 
                v-model="formData.last_name"
                type="text" 
                required
                :readonly="isCreateAccountMode"
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                :class="{'opacity-70 cursor-not-allowed': isCreateAccountMode}"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Adresse Email</label>
            <input 
              v-model="formData.email"
              type="email" 
              required
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
              <input 
                v-model="formData.phone"
                type="tel" 
                :readonly="isCreateAccountMode"
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                :class="{'opacity-70 cursor-not-allowed': isCreateAccountMode}"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rôles</label>
              <select 
                v-model="formData.role_names"
                required
                multiple
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition h-32"
              >
                <option value="" disabled>Sélectionner un rôle</option>
                <option v-for="role in availableRoles" :key="role" :value="role">
                  {{ role }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Feedback on Create -->
        <div v-if="tempPassword" class="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p class="text-sm text-green-800 font-medium mb-1">Utilisateur créé avec succès !</p>
          <p class="text-xs text-green-700">Mot de passe temporaire : <span class="font-mono font-bold">{{ tempPassword }}</span></p>
          <p class="text-xs text-green-600 mt-1 italic">Veuillez le communiquer à l'utilisateur.</p>
        </div>

        <div v-if="error" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {{ error }}
        </div>

        <div class="mt-8 flex justify-end gap-3">
          <button 
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg transition"
          >
            Annuler
          </button>
          <button 
            type="submit"
            :disabled="loading"
            class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50"
          >
            {{ loading ? 'Enregistrement...' : (isCreateAccountMode ? 'Créer le compte' : (isEdit ? 'Mettre à jour' : 'Créer')) }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import api from '@/services/api';
import { userService, type User, type UserCreate, type UserUpdate } from '@/services/userService';

const props = defineProps<{
  user?: User | null;
  isCreateAccountMode?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const isEdit = computed(() => !!props.user);
const loading = ref(false);
const error = ref('');
const tempPassword = ref('');
const departments = ref<any[]>([]);
const usersList = ref<User[]>([]);

// Rôles disponibles
const availableRoles = [
  'Admin',
  'Direction',
  'RH / Comptabilité',
  'Achats',
  'Chef de Projet',
  "Chef d'Equipe",
  'Commercial',
  'Qualité',
  'Employé'
];

const formData = ref({
  name: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  role_names: [] as string[]
});

onMounted(async () => {
  if (props.user) {
    formData.value = {
      name: props.user.name,
      first_name: props.user.first_name || '',
      last_name: props.user.last_name || '',
      email: props.user.email,
      phone: props.user.phone || '',
      role_names: props.user.roles?.map(r => r.name) || []
    };
  }
});

const handleSubmit = async () => {
  loading.value = true;
  error.value = '';
  tempPassword.value = '';

  try {
    if (props.isCreateAccountMode && props.user) {
      const response = await userService.createAccountForEmployee(props.user.id, formData.value.email, formData.value.role_names);
      tempPassword.value = response.temporary_password || '';
    } else if (isEdit.value && props.user) {
      await userService.updateUser(props.user.id, formData.value as UserUpdate);
      emit('saved');
    } else {
      const response = await userService.createUser(formData.value as UserCreate);
      tempPassword.value = response.temporary_password || '';

    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Une erreur est survenue.";
  } finally {
    loading.value = false;
  }
};
</script>
