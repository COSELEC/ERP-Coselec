<template>
  <div class="overflow-x-auto">
    <table class="w-full text-left text-sm text-gray-500">
      <thead class="bg-gray-50 text-xs text-gray-700 uppercase border-b border-gray-100">
        <tr>
          <th v-for="col in columns" :key="col.key" scope="col" class="px-6 py-4 font-semibold" :class="col.headerClass">
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading" class="bg-white border-b border-gray-50">
          <td :colspan="columns.length" class="px-6 py-12 text-center text-gray-400">
            Chargement...
          </td>
        </tr>
        
        <tr v-else-if="items.length === 0" class="bg-white border-b border-gray-50">
          <td :colspan="columns.length" class="px-6 py-12 text-center text-gray-400">
            {{ emptyMessage }}
          </td>
        </tr>

        <tr 
          v-else
          v-for="item in items" 
          :key="item.id || Math.random()" 
          @click="emit('rowClick', item)"
          class="bg-white border-b border-gray-50 hover:bg-gray-50/50 transition cursor-pointer"
        >
          <td v-for="col in columns" :key="col.key" class="px-6 py-4" :class="col.cellClass">
            <slot :name="col.key" :item="item" :value="item[col.key]">
              {{ item[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
export interface ColumnDefinition {
  key: string;
  label: string;
  headerClass?: string;
  cellClass?: string;
}

defineProps<{
  columns: ColumnDefinition[];
  items: any[];
  loading?: boolean;
  emptyMessage?: string;
}>();

const emit = defineEmits<{
  (e: 'rowClick', item: any): void
}>();
</script>
