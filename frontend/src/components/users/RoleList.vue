<template>
  <AppTable 
    :columns="columns" 
    :items="roles" 
    :loading="loading" 
    emptyMessage="Aucun rôle trouvé."
  >
    <!-- Custom slot for the Name column to add badges -->
    <template #name="{ item }">
      <span 
        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
        :class="getRoleColor(item.name)"
      >
        {{ item.name }}
      </span>
    </template>

    <!-- Custom slot for Permissions count -->
    <template #permissions="{ item }">
      <span class="text-xs text-gray-500">{{ item.permissions.length }} permission(s)</span>
    </template>

    <!-- Custom slot for Actions -->
    <template #actions="{ item }">
      <div class="text-right">
        <button 
          @click="$emit('edit', item)"
          class="font-medium text-blue-600 hover:text-blue-800 transition mr-4"
        >
          Éditer
        </button>
        <button 
          v-if="item.name !== 'Admin'"
          @click="$emit('delete', item)"
          class="font-medium text-red-600 hover:text-red-800 transition"
        >
          Supprimer
        </button>
      </div>
    </template>
  </AppTable>
</template>

<script setup lang="ts">
import type { Role } from '@/services/roleService';
import AppTable, { type ColumnDefinition } from '@/components/common/AppTable.vue';

defineProps<{
  roles: Role[];
  loading: boolean;
}>();

defineEmits<{
  (e: 'edit', role: Role): void;
  (e: 'delete', role: Role): void;
}>();

const columns: ColumnDefinition[] = [
  { key: 'name', label: 'Nom du rôle', cellClass: 'font-medium text-gray-900' },
  { key: 'description', label: 'Description' },
  { key: 'permissions', label: 'Permissions' },
  { key: 'actions', label: 'Actions', headerClass: 'text-right' }
];

const getRoleColor = (roleName: string) => {
  switch (roleName) {
    case 'Admin': return 'bg-purple-100 text-purple-800';
    case 'Employé': return 'bg-blue-100 text-blue-800';
    case 'RH / Comptabilité': return 'bg-green-100 text-green-800';
    case 'Direction': return 'bg-orange-100 text-orange-800';
    case 'Achats': return 'bg-yellow-100 text-yellow-800';
    case 'Chef de Projet': return 'bg-indigo-100 text-indigo-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};
</script>
