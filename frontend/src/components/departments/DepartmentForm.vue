<template>
  <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden transform transition-all">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-bold text-gray-900">
          {{ isEdit ? 'Modifier Département' : 'Nouveau Département' }}
        </h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom du département *</label>
            <input 
              v-model="formData.name"
              type="text" 
              required
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Code (optionnel)</label>
            <input 
              v-model="formData.code"
              type="text" 
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            />
          </div>
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

const props = defineProps<{
  department?: any | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved'): void;
}>();

const isEdit = computed(() => !!props.department);
const loading = ref(false);
const error = ref('');

const formData = ref({
  name: '',
  code: ''
});

onMounted(() => {
  if (props.department) {
    formData.value = {
      name: props.department.name,
      code: props.department.code || ''
    };
  }
});

const handleSubmit = async () => {
  loading.value = true;
  error.value = '';

  try {
    if (isEdit.value && props.department) {
      await api.put(`/departments/${props.department.id}`, formData.value);
    } else {
      await api.post('/departments', formData.value);
    }
    emit('saved');
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Une erreur est survenue.";
  } finally {
    loading.value = false;
  }
};
</script>
