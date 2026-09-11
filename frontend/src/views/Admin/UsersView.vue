<template>
  <AppLayout>
    <div class="h-full bg-gray-50 p-3 sm:p-4">
      <header class="mb-10 flex justify-between items-end">
        <div>
          <h1 class="text-xl font-bold text-gray-900 tracking-tight">Gestion des Utilisateurs</h1>
          <p class="text-sm text-gray-400 mt-1">Administration des accès et rôles</p>
        </div>
        <button 
          @click="openCreateForm"
          class="bg-red-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
        >
          + Nouvel Utilisateur
        </button>
      </header>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <!-- Utilisateurs -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
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
            @promote="promoteToEmployee"
            @reset-password="openResetPasswordForm"
          />

          <!-- Pagination -->
          <AppPagination 
            :currentPage="currentPage" 
            :totalPages="totalPages" 
            @change="changePage" 
          />
        </div>

        <!-- Employés sans compte -->
        <div class="bg-white rounded-xl shadow-sm border border-orange-100 p-4">
          <div class="mb-6 flex justify-between items-center">
            <h2 class="text-lg font-bold text-orange-600">Employés sans compte</h2>
            <input 
              v-model="searchEmployeesQuery"
              @input="handleSearchEmployees"
              type="text" 
              placeholder="Rechercher employé..."
              class="max-w-xs px-4 py-2 border border-orange-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition"
            />
          </div>

          <UserList 
            :users="employeesNoAccount" 
            :loading="loadingEmployees"
            :currentUserId="currentUserId"
            :isEmployeeNoAccount="true"
            @create-account="openCreateAccountForm"
          />

          <!-- Pagination -->
          <AppPagination 
            :currentPage="currentPageEmployees" 
            :totalPages="totalPagesEmployees" 
            @change="changePageEmployees" 
          />
        </div>
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
            class="bg-red-600 hover:bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            + Nouveau Rôle
          </button>
        </header>

        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <RoleList 
            :roles="roles" 
            :loading="loadingRoles"
            @edit="openRoleEditForm" 
            @delete="confirmRoleDelete" 
          />
        </div>
      </div>

      <!-- Section des Départements -->
      <div class="mt-12">
        <header class="mb-6 flex justify-between items-end">
          <div>
            <h2 class="text-xl font-bold text-gray-900 tracking-tight">Gestion des Départements</h2>
            <p class="text-sm text-gray-400 mt-1">Gérez les directions et services de l'entreprise</p>
          </div>
          <button 
            @click="openDeptCreateForm"
            class="bg-red-600 hover:bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            + Nouveau Département
          </button>
        </header>

        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <DepartmentList 
            :departments="departments" 
            :loading="loadingDepts"
            @edit="openDeptEditForm" 
            @delete="confirmDeptDelete" 
          />
        </div>
      </div>
    </div>

    <!-- Modal Form Utilisateur -->
    <UserForm 
      v-if="showUserForm"
      :user="selectedUser"
      :isCreateAccountMode="isCreateAccountMode"
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

    <!-- Modal Form Département -->
    <DepartmentForm 
      v-if="showDeptForm"
      :department="selectedDept"
      @close="closeDeptForm"
      @saved="onDeptSaved"
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
import DepartmentList from '@/components/departments/DepartmentList.vue';
import DepartmentForm from '@/components/departments/DepartmentForm.vue';
import ResetPasswordModal from '@/components/users/ResetPasswordModal.vue';
import { userService, type User } from '@/services/userService';
import { roleService, type Role } from '@/services/roleService';
import api from '@/services/api';
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
const isCreateAccountMode = ref(false);

const showResetModal = ref(false);
const userForReset = ref<User | null>(null);

let searchTimeout: ReturnType<typeof setTimeout>;

// Employees No Account state
const employeesNoAccount = ref<User[]>([]);
const loadingEmployees = ref(true);
const totalPagesEmployees = ref(1);
const currentPageEmployees = ref(1);
const searchEmployeesQuery = ref('');
let searchEmployeesTimeout: ReturnType<typeof setTimeout>;

// Roles state
const roles = ref<Role[]>([]);
const loadingRoles = ref(true);
const showRoleForm = ref(false);
const selectedRole = ref<Role | null>(null);

// Departments state
const departments = ref<any[]>([]);
const loadingDepts = ref(true);
const showDeptForm = ref(false);
const selectedDept = ref<any | null>(null);

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

const fetchEmployeesNoAccount = async (page = 1) => {
  loadingEmployees.value = true;
  try {
    const skip = (page - 1) * limit;
    const response = await api.get('/users/employees-no-account', {
      params: { skip, limit, search: searchEmployeesQuery.value }
    });
    employeesNoAccount.value = response.data.items;
    totalPagesEmployees.value = response.data.total > 0 ? Math.ceil(response.data.total / limit) : 1;
    currentPageEmployees.value = page;
  } catch (error) {
    console.error('Failed to fetch employees without account:', error);
  } finally {
    loadingEmployees.value = false;
  }
};

const fetchDepartments = async () => {
  loadingDepts.value = true;
  try {
    const res = await api.get('/departments');
    departments.value = res.data;
  } catch (error) {
    console.error('Failed to fetch departments:', error);
  } finally {
    loadingDepts.value = false;
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
  isCreateAccountMode.value = false;
  showUserForm.value = true;
};

const openEditForm = (user: User) => {
  selectedUser.value = user;
  isCreateAccountMode.value = false;
  showUserForm.value = true;
};

const closeUserForm = () => {
  showUserForm.value = false;
  selectedUser.value = null;
  isCreateAccountMode.value = false;
};

const onUserSaved = () => {
  closeUserForm();
  fetchUsers(currentPage.value);
  fetchEmployeesNoAccount(currentPageEmployees.value);
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

const promoteToEmployee = async (user: User) => {
  if (confirm(`Êtes-vous sûr de vouloir promouvoir ${user.name} en employé ? Il apparaitra désormais dans la liste des employés et ses informations RH pourront être renseignées.`)) {
    try {
      await userService.updateUser(user.id, { is_employee: true });
      fetchUsers(currentPage.value);
      toast.success(`${user.name} a été promu en employé avec succès.`);
    } catch (error) {
      console.error('Failed to promote user:', error);
      toast.error("Erreur lors de la promotion de l'utilisateur.");
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

const openCreateAccountForm = (user: User) => {
  selectedUser.value = user;
  isCreateAccountMode.value = true;
  showUserForm.value = true;
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

// Departments Handlers
const openDeptCreateForm = () => {
  selectedDept.value = null;
  showDeptForm.value = true;
};

const openDeptEditForm = (dept: any) => {
  selectedDept.value = dept;
  showDeptForm.value = true;
};

const closeDeptForm = () => {
  showDeptForm.value = false;
  selectedDept.value = null;
};

const onDeptSaved = () => {
  closeDeptForm();
  fetchDepartments();
};

const confirmDeptDelete = async (dept: any) => {
  if (confirm(`Êtes-vous sûr de vouloir supprimer le département ${dept.name} ?`)) {
    try {
      await api.delete(`/departments/${dept.id}`);
      fetchDepartments();
      toast.success("Département supprimé avec succès.");
    } catch (error: any) {
      console.error('Failed to delete department:', error);
      toast.error(error.response?.data?.detail || "Erreur lors de la suppression du département.");
    }
  }
};

const handleSearchEmployees = () => {
  clearTimeout(searchEmployeesTimeout);
  searchEmployeesTimeout = setTimeout(() => {
    fetchEmployeesNoAccount(1);
  }, 500);
};

const changePageEmployees = (page: number) => {
  if (page >= 1 && page <= totalPagesEmployees.value) {
    fetchEmployeesNoAccount(page);
  }
};

// ...
onMounted(() => {
  fetchUsers();
  fetchEmployeesNoAccount();
  fetchRoles();
  fetchDepartments();
});
</script>
