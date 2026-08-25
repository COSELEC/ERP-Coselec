<template>
  <div class="mt-6 flex items-center justify-between border-t border-gray-100 pt-4" v-if="totalPages > 1">
    <button 
      :disabled="currentPage === 1"
      @click="$emit('change', currentPage - 1)"
      class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition"
    >
      Précédent
    </button>
    <span class="text-sm text-gray-500">Page {{ currentPage }} sur {{ totalPages }}</span>
    <button 
      :disabled="currentPage === totalPages"
      @click="$emit('change', currentPage + 1)"
      class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition"
    >
      Suivant
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentPage: number;
  totalPages: number;
}>();

defineEmits<{
  (e: 'change', page: number): void;
}>();
</script>
