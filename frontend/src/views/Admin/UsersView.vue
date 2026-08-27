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
          @reset-password="openResetPasswordForm"
        />

        <!-- Pagination -->
        <AppPagination 
          :currentPage="currentPage" 
          :totalPages="totalPages" 
          @change="changePage" 
        />
      </div>
      
      <!-- Section des Rôles -->
      <div class="mt-12">
        <header class="mb-6 flex justify-between items-end">
          <div>
            <h2 class="text-xl font-bold text-gray-900 tracking-tight">Gestion des Rôles</h2>
            <p class="text-sm text-gray-400 mt-1">Gérez les rôles et leurs permissions</p>
          </div>
          <button 
            @click="openRoleCreateForm"
            class="bg-gray-800 hover:bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            + Nouveau Rôle
          </button>
        </header>

        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <RoleList 
            :roles="roles" 
            :loading="loadingRoles"
            @edit="openRoleEditForm" 
            @delete="confirmRoleDelete" 
          />
        </div>
      </div>
    </div>

    <!-- Modal Form Utilisateur -->
    <UserForm 
      v-if="showUserForm"
      :user="selectedUser"
      @close="closeUserForm"
      @saved="onUserSaved"
    />

    <!-- Modal Form Rôle -->
    <RoleForm 
      v-if="showRoleForm"
      :role="selectedRole"
      @close="closeRoleForm"
      @saved="onRoleSaved"
    />

    <!-- Modal Reset Password -->
    <ResetPasswordModal
      v-if="showResetModal"
      :isOpen="showResetModal"
      :userEmail="userForReset?.email || ''"
      @close="closeResetPasswordForm"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import UserList from '@/components/users/UserList.vue';
import UserForm from '@/components/users/UserForm.vue';
import AppPagination from '@/components/common/AppPagination.vue';
import RoleList from '@/components/users/RoleList.vue';
import RoleForm from '@/components/users/RoleForm.vue';
import ResetPasswordModal from '@/components/users/ResetPasswordModal.vue';
import { userService, type User } from '@/services/userService';
import { roleService, type Role } from '@/services/roleService';
import { getStoredProfile } from '@/services/session';
import { useToast } from '@/composables/useToast';

const toast = useToast();

const profile = getStoredProfile();
const currentUserId = profile?.id;

// Users state
const users = ref<User[]>([]);
const loading = ref(true);
const totalPages = ref(1);
const currentPage = ref(1);
const limit = 10;
const searchQuery = ref('');

const showUserForm = ref(false);
const selectedUser = ref<User | null>(null);

const showResetModal = ref(false);
const userForReset = ref<User | null>(null);

let searchTimeout: ReturnType<typeof setTimeout>;

// Roles state
const roles = ref<Role[]>([]);
const loadingRoles = ref(true);
const showRoleForm = ref(false);
const selectedRole = ref<Role | null>(null);

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

const fetchRoles = async () => {
  loadingRoles.value = true;
  try {
    roles.value = await roleService.getRoles();
  } catch (error) {
    console.error('Failed to fetch roles:', error);
  } finally {
    loadingRoles.value = false;
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

// Users Handlers
const openCreateForm = () => {
  selectedUser.value = null;
  showUserForm.value = true;
};

const openEditForm = (user: User) => {
  selectedUser.value = user;
  showUserForm.value = true;
};

const closeUserForm = () => {
  showUserForm.value = false;
  selectedUser.value = null;
};

const onUserSaved = () => {
  closeUserForm();
  fetchUsers(currentPage.value);
};

const confirmDelete = async (user: User) => {
  if (confirm(`Êtes-vous sûr de vouloir supprimer ${user.name} ? Cette action est irréversible.`)) {
    try {
      await userService.deleteUser(user.id);
      fetchUsers(currentPage.value);
      toast.success("Utilisateur supprimé avec succès.");
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error("Erreur lors de la suppression de l'utilisateur.");
    }
  }
};

const openResetPasswordForm = (user: User) => {
  userForReset.value = user;
  showResetModal.value = true;
};

const closeResetPasswordForm = () => {
  showResetModal.value = false;
  userForReset.value = null;
};


// Roles Handlers
const openRoleCreateForm = () => {
  selectedRole.value = null;
  showRoleForm.value = true;
};

const openRoleEditForm = (role: Role) => {
  selectedRole.value = role;
  showRoleForm.value = true;
};

const closeRoleForm = () => {
  showRoleForm.value = false;
  selectedRole.value = null;
};

const onRoleSaved = () => {
  closeRoleForm();
  fetchRoles();
};

const confirmRoleDelete = async (role: Role) => {
  if (confirm(`Êtes-vous sûr de vouloir supprimer le rôle ${role.name} ?`)) {
    try {
      await roleService.deleteRole(role.id);
      fetchRoles();
      toast.success("Rôle supprimé avec succès.");
    } catch (error: any) {
      console.error('Failed to delete role:', error);
      toast.error(error.response?.data?.detail || "Erreur lors de la suppression du rôle.");
    }
  }
};

onMounted(() => {
  fetchUsers();
  fetchRoles();
});
</script>
