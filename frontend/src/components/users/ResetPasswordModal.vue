<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        Réinitialiser le mot de passe
      </h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Utilisateur : <span class="font-medium text-gray-700 dark:text-gray-200">{{ userEmail }}</span>
      </p>

      <!-- Message d'erreur -->
      <div v-if="errorMessage" class="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
        {{ errorMessage }}
      </div>

      <div v-if="showConfirm" class="mt-8 text-center">
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-6">
          Vous confirmez la réinitialisation du mot de passe pour cet utilisateur ?
        </p>
        <div class="flex justify-center space-x-3">
          <button
            type="button"
            @click="showConfirm = false"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Non, annuler
          </button>
          <button
            type="button"
            @click="executeReset"
            :disabled="loading"
            class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {{ loading ? 'En cours...' : 'Oui, réinitialiser' }}
          </button>
        </div>
      </div>

      <form v-else @submit.prevent="handlePreSubmit" class="mt-4 space-y-4">
        <!-- Nouveau mot de passe -->
        <div>
          <div class="flex items-center justify-between">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Nouveau mot de passe
            </label>
            <button
              type="button"
              @click="generateRandomPassword"
              class="text-xs text-blue-600 hover:underline dark:text-blue-400"
            >
              Générer un mot de passe
            </button>
          </div>
          <input
            v-model="newPassword"
            type="text"
            required
            placeholder="Entrez le nouveau mot de passe"
            class="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Confirmer le mot de passe -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Confirmer le mot de passe
          </label>
          <input
            v-model="confirmPassword"
            type="text"
            required
            placeholder="Confirmez le nouveau mot de passe"
            class="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <p class="text-xs text-amber-600 dark:text-amber-400">
        </p>

        <!-- Actions -->
        <div class="mt-6 flex justify-end space-x-3">
          <button
            type="button"
            @click="$emit('close')"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Annuler
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {{ loading ? 'En cours...' : 'Réinitialiser' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { userService } from '@/services/userService';
import { useToast } from '@/composables/useToast';

const props = defineProps<{
  isOpen: boolean;
  userEmail: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'success'): void;
}>();

const { addToast } = useToast();

const newPassword = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const errorMessage = ref('');

// Génère un mot de passe aléatoire de 12 caractères
const generateRandomPassword = () => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
  let pass = '';
  for (let i = 0; i < 12; i++) {
    pass += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  newPassword.value = pass;
  confirmPassword.value = pass;
};

const showConfirm = ref(false);

const handlePreSubmit = () => {
  errorMessage.value = '';

  if (!newPassword.value || newPassword.value.length < 6) {
    errorMessage.value = 'Le mot de passe doit contenir au moins 6 caractères.';
    return;
  }

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Les mots de passe ne correspondent pas.';
    return;
  }

  showConfirm.value = true;
};

const executeReset = async () => {
  errorMessage.value = '';

  if (!newPassword.value || newPassword.value.length < 6) {
    errorMessage.value = 'Le mot de passe doit contenir au moins 6 caractères.';
    return;
  }

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Les mots de passe ne correspondent pas.';
    return;
  }

  loading.value = true;
  try {
    await userService.adminResetPassword({
      email: props.userEmail,
      new_password: newPassword.value,
    });

    addToast(
      `Mot de passe réinitialisé pour ${props.userEmail}`,
      'success'
    );

    newPassword.value = '';
    confirmPassword.value = '';
    showConfirm.value = false;
    emit('success');
    emit('close');
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Erreur lors de la réinitialisation';
  } finally {
    loading.value = false;
  }
};
</script>