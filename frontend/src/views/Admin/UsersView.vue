<template>
  <AppLayout>
    <div class="min-h-screen bg-gray-50 p-8">
      <header class="mb-10 flex justify-between items-end">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Gestion des Utilisateurs</h1>
          <p class="text-sm text-gray-400 mt-1">Administration des accès et rôles</p>
        </div>
        <button 
          @click="openCreateForm"
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
        >
          + Nouvel Utilisateur
        </button>
      </header>

      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div class="mb-6 flex gap-4">
          <input 
            v-model="searchQuery"
            @input="handleSearch"
            type="text" 
            placeholder="Rechercher par nom ou email..."
            class="flex-1 max-w-md px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          />
        </div>

        <UserList 
          :users="users" 
          :loading="loading"
          :currentUserId="currentUserId"
          @edit="openEditForm" 
          @delete="confirmDelete" 
        />

        <!-- Pagination -->
        <div class="mt-6 flex items-center justify-between border-t border-gray-100 pt-4" v-if="totalPages > 1">
          <button 
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
            class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition"
          >
            Précédent
          </button>
          <span class="text-sm text-gray-500">Page {{ currentPage }} sur {{ totalPages }}</span>
          <button 
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
            class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition"
          >
            Suivant
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Form -->
    <UserForm 
      v-if="showForm"
      :user="selectedUser"
      @close="closeForm"
      @saved="onUserSaved"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import UserList from '@/components/users/UserList.vue';
import UserForm from '@/components/users/UserForm.vue';
import { userService, type User } from '@/services/userService';
import { getStoredProfile } from '@/services/session';
import { useToast } from '@/composables/useToast';

const toast = useToast();

const profile = getStoredProfile();
const currentUserId = profile?.id;

const users = ref<User[]>([]);
const loading = ref(true);
const totalPages = ref(1);
const currentPage = ref(1);
const limit = 10;
const searchQuery = ref('');

const showForm = ref(false);
const selectedUser = ref<User | null>(null);

let searchTimeout: any;

const fetchUsers = async (page = 1) => {
  loading.value = true;
  try {
    const skip = (page - 1) * limit;
    const response = await userService.getUsers(skip, limit, searchQuery.value);
    users.value = response.items;
    totalPages.value = Math.ceil(response.total / limit);
    currentPage.value = page;
  } catch (error) {
    console.error('Failed to fetch users:', error);
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    fetchUsers(1);
  }, 500);
};

const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    fetchUsers(page);
  }
};

const openCreateForm = () => {
  selectedUser.value = null;
  showForm.value = true;
};

const openEditForm = (user: User) => {
  selectedUser.value = user;
  showForm.value = true;
};

const closeForm = () => {
  showForm.value = false;
  selectedUser.value = null;
};

const onUserSaved = () => {
  closeForm();
  fetchUsers(currentPage.value);
};

const confirmDelete = async (user: User) => {
  if (confirm(`Êtes-vous sûr de vouloir supprimer ${user.name} ? Cette action est irréversible.`)) {
    try {
      await userService.deleteUser(user.id);
      fetchUsers(currentPage.value);
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error("Erreur lors de la suppression de l'utilisateur.");
    }
  }
};

onMounted(() => {
  fetchUsers();
});
</script>
