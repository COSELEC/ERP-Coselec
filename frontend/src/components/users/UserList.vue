<template>
  <AppTable 
    :columns="columns" 
    :items="users" 
    :loading="loading" 
    emptyMessage="Aucun utilisateur trouvé."
  >
    <!-- Custom slot for the Role column -->
    <template #roles="{ item }">
      <span 
        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
        :class="getRoleColor(item.roles?.[0]?.name)"
      >
        {{ item.roles?.[0]?.name || 'Sans rôle' }}
      </span>
    </template>

    <!-- Custom slot for Actions avec menu 3 points -->
    <template #actions="{ item }">
      <div class="relative flex justify-end items-center">
        <button 
          @click="toggleDropdown(item.id)"
          @blur="closeDropdownDelayed"
          class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition focus:outline-none"
          title="Options"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
          </svg>
        </button>

        <!-- Menu déroulant -->
        <div 
          v-show="openDropdownId === item.id"
          class="absolute right-0 top-full mt-1 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-50 overflow-hidden"
        >
          <div class="py-1">
            <button 
              @click="$emit('edit', item); openDropdownId = null"
              class="flex w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition"
            >
              Éditer
            </button>
            <button 
              @click="$emit('reset-password', item); openDropdownId = null"
              class="flex w-full px-4 py-2 text-sm text-amber-600 hover:bg-amber-50 transition"
            >
              Réinitialiser le mot de passe
            </button>
            <button 
              v-if="item.id !== currentUserId"
              @click="$emit('delete', item); openDropdownId = null"
              class="flex w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition"
            >
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </template>
  </AppTable>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { User } from '@/services/userService';
import AppTable, { type ColumnDefinition } from '@/components/common/AppTable.vue';

defineProps<{
  users: User[];
  loading: boolean;
  currentUserId?: number;
}>();

defineEmits<{
  (e: 'edit', user: User): void;
  (e: 'delete', user: User): void;
  (e: 'reset-password', user: User): void;
}>();

const columns: ColumnDefinition[] = [
  { key: 'name', label: 'Nom', cellClass: 'font-medium text-gray-900' },
  { key: 'email', label: 'Email' },
  { key: 'roles', label: 'Rôle' },
  { key: 'actions', label: 'Actions', headerClass: 'text-right' }
];

const getRoleColor = (roleName: string | undefined) => {
  if (!roleName) return 'bg-gray-100 text-gray-800';
  
  switch (roleName) {
    case 'Admin': return 'bg-purple-100 text-purple-800';
    case 'Employe': return 'bg-blue-100 text-blue-800';
    case 'RH': return 'bg-green-100 text-green-800';
    case 'Direction': return 'bg-orange-100 text-orange-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const openDropdownId = ref<number | null>(null);

const toggleDropdown = (id: number) => {
  openDropdownId.value = openDropdownId.value === id ? null : id;
};

const closeDropdownDelayed = () => {
  setTimeout(() => {
    openDropdownId.value = null;
  }, 200);
};
</script>