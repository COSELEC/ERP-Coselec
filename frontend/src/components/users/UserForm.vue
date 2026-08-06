<template>
  <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden transform transition-all">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-bold text-gray-900">
          {{ isEdit ? 'Modifier Utilisateur' : 'Nouvel Utilisateur' }}
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
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
              <input 
                v-model="formData.last_name"
                type="text" 
                required
                class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
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

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Rôle</label>
            <select 
              v-model="formData.role_name"
              required
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            >
              <option value="" disabled>Sélectionner un rôle</option>
              <option v-for="role in availableRoles" :key="role" :value="role">
                {{ role }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Département</label>
            <select 
              v-model="formData.department_id"
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            >
              <option value="" disabled>Sélectionner un département</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                {{ dept.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Statut</label>
            <select 
              v-model="formData.status"
              required
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            >
              <option value="CDI">CDI</option>
              <option value="CDD">CDD</option>
              <option value="STAGIAIRE">Stagiaire</option>
              <option value="PRESTATAIRE">Prestataire</option>
              <option value="INACTIF">Inactif</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Manager</label>
            <select 
              v-model="formData.manager_id"
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            >
              <option :value="undefined">Aucun</option>
              <option 
                v-for="mgr in availableManagers" 
                :key="mgr.id" 
                :value="mgr.id"
              >
                {{ mgr.first_name || '' }} {{ mgr.last_name || mgr.name || '' }}
              </option>
            </select>
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
            {{ loading ? 'Enregistrement...' : (isEdit ? 'Mettre à jour' : 'Créer') }}
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

// Ces rôles pourraient aussi venir de l'API dans un cas réel
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

const availableManagers = computed(() => {
  if (isEdit.value && props.user) {
    return usersList.value.filter(u => u.id !== props.user?.id);
  }
  return usersList.value;
});

const formData = ref({
  name: '',
  first_name: '',
  last_name: '',
  status: 'CDI',
  email: '',
  role_name: '',
  department_id: undefined as number | undefined,
  manager_id: undefined as number | null | undefined
});

onMounted(async () => {
  try {
    const deptRes = await api.get('/departments');
    const allowedDepts = ['Achats', 'RH', 'Travaux', 'Etudes', 'Informatique'];
    departments.value = deptRes.data.filter((d: any) => allowedDepts.includes(d.name));
    
    // Fetch users for manager list
    const usersRes = await userService.getUsers(0, 100);
    usersList.value = usersRes.items;
  } catch (err) {
    console.error('Erreur lors du chargement des données (départements ou utilisateurs)', err);
  }

  if (props.user) {
    formData.value = {
      name: props.user.name,
      first_name: props.user.first_name || '',
      last_name: props.user.last_name || '',
      status: props.user.status || 'CDI',
      email: props.user.email,
      role_name: props.user.roles?.[0]?.name || '',
      department_id: props.user.department_id,
      manager_id: props.user.manager_id
    };
  }
});

const handleSubmit = async () => {
  loading.value = true;
  error.value = '';
  tempPassword.value = '';

  try {
    if (isEdit.value && props.user) {
      await userService.updateUser(props.user.id, formData.value as UserUpdate);
      emit('saved');
    } else {
      const response = await userService.createUser(formData.value as UserCreate);
      tempPassword.value = response.temporary_password || '';
      // On ne ferme pas immédiatement la modale pour que l'admin puisse voir le mot de passe temp.
      // S'il ferme lui-même, la liste sera rafraichie car on peut émettre saved lors du close s'il y a un mot de passe.
      // Mais modifions plutôt : on affiche le mdp et on change le bouton "Fermer".
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Une erreur est survenue.";
  } finally {
    loading.value = false;
  }
};
</script>
