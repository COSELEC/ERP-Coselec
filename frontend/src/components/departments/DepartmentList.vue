<template>
  <div>
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-10 bg-gray-200 rounded w-full"></div>
      <div class="h-10 bg-gray-200 rounded w-full"></div>
    </div>
    
    <div v-else-if="departments.length === 0" class="text-center py-8 text-gray-500">
      Aucun département trouvé.
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100 text-gray-500 text-xs uppercase tracking-wider">
            <th class="p-4 font-medium rounded-tl-lg">Nom</th>
            <th class="p-4 font-medium">Code</th>
            <th class="p-4 font-medium text-right rounded-tr-lg">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr 
            v-for="dept in departments" 
            :key="dept.id"
            class="hover:bg-gray-50/50 transition-colors"
          >
            <td class="p-4 font-medium text-gray-900">{{ dept.name }}</td>
            <td class="p-4 text-gray-600">{{ dept.code || '-' }}</td>
            <td class="p-4 text-right">
              <div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity" style="opacity: 1">
                <button 
                  @click="$emit('edit', dept)"
                  class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                  title="Modifier"
                >
                  <span class="material-symbols-outlined text-[20px]">edit</span>
                </button>
                <button 
                  @click="$emit('delete', dept)"
                  class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                  title="Supprimer"
                >
                  <span class="material-symbols-outlined text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  departments: any[];
  loading: boolean;
}>();

defineEmits<{
  (e: 'edit', department: any): void;
  (e: 'delete', department: any): void;
}>();
</script>
