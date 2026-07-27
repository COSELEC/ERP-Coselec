<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-2xl shadow-sm border border-gray-100">
    
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-gray-900">Nouvelle Demande</h2>
      <p class="text-sm text-gray-500 mt-1">Soumettez une requête informatique ou d'intervention technique.</p>
    </div>

    <form @submit.prevent="submitRequest" class="space-y-8">
      
      <!-- General Section -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <!-- Main Category / Request Type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Catégorie de la demande</label>
          <div class="flex gap-4">
            <button 
              type="button"
              @click="mainCategory = 'IT'"
              class="flex-1 py-3 px-4 border rounded-xl flex items-center justify-center gap-2 transition-all"
              :class="mainCategory === 'IT' ? 'bg-indigo-600 text-white border-indigo-600 shadow-md' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clip-rule="evenodd" />
              </svg>
              Informatique (IT)
            </button>
            <button 
              type="button"
              @click="mainCategory = 'FACILITY'"
              class="flex-1 py-3 px-4 border rounded-xl flex items-center justify-center gap-2 transition-all"
              :class="mainCategory === 'FACILITY' ? 'bg-amber-500 text-white border-amber-500 shadow-md' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
              </svg>
              Services Généraux
            </button>
          </div>
        </div>

        <!-- Priority / Urgence Globale -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Niveau d'urgence global</label>
          <div class="relative">
            <select v-model="requestData.priority" class="block w-full rounded-xl border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 border pl-3 pr-10 appearance-none">
              <option value="LOW">Bas</option>
              <option value="NORMAL">Moyen</option>
              <option value="HIGH">Haut</option>
              <option value="URGENT">Bloquant (Urgent)</option>
            </select>
            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
              <span :class="priorityBadgeClass" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                {{ requestData.priority }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <hr class="border-gray-100" />

      <!-- Dynamic Form Fields Component Injection -->
      <div class="min-h-[300px]">
        <Transition name="fade" mode="out-in">
          <ITRequestFields 
            v-if="mainCategory === 'IT'" 
            v-model="requestData.payload" 
          />
          <FacilityRequestFields 
            v-else-if="mainCategory === 'FACILITY'" 
            v-model="requestData.payload" 
          />
        </Transition>
      </div>

      <hr class="border-gray-100" />

      <!-- Global Description (Optional override or additional notes) -->
      <div>
        <label class="block text-sm font-medium text-gray-700">Notes complémentaires (Optionnel)</label>
        <textarea 
          v-model="requestData.description" 
          rows="2" 
          class="mt-1 block w-full rounded-xl border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 border"
          placeholder="Toute autre information utile pour le traitement de la demande..."
        ></textarea>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-end gap-4 pt-4">
        <button type="button" class="text-sm font-medium text-gray-600 hover:text-gray-900">
          Annuler
        </button>
        <button 
          type="submit" 
          :disabled="isSubmitting"
          class="inline-flex justify-center rounded-xl border border-transparent bg-indigo-600 py-3 px-6 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <svg v-if="isSubmitting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Soumettre la demande
        </button>
      </div>
      
      <!-- Success/Error Message -->
      <div v-if="statusMessage" :class="statusMessage.type === 'error' ? 'bg-red-50 text-red-800' : 'bg-green-50 text-green-800'" class="p-4 rounded-xl text-sm font-medium mt-4">
        {{ statusMessage.text }}
      </div>

    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import ITRequestFields from './ITRequestFields.vue'
import FacilityRequestFields from './FacilityRequestFields.vue'

// --- State ---
const mainCategory = ref('IT') // 'IT' or 'FACILITY'
const isSubmitting = ref(false)
const statusMessage = ref(null)

// The generic request wrapper state
const requestData = reactive({
  priority: 'NORMAL',
  description: '',
  category: '', // Used for top-level category if needed
  project_id: null,
  payload: {} // Handled by child components
})

// --- Reset Payload when category changes ---
watch(mainCategory, (newCat) => {
  requestData.payload = {}
  requestData.category = newCat // e.g. IT or FACILITY
})

// --- Computed ---
const priorityBadgeClass = computed(() => {
  const map = {
    'LOW': 'bg-gray-100 text-gray-800',
    'NORMAL': 'bg-blue-100 text-blue-800',
    'HIGH': 'bg-orange-100 text-orange-800',
    'URGENT': 'bg-red-100 text-red-800 font-bold animate-pulse'
  }
  return map[requestData.priority] || map['NORMAL']
})

// --- Methods ---
const submitRequest = async () => {
  isSubmitting.value = true
  statusMessage.value = null

  // Ensure the top-level 'type' matches the payload's type for the backend
  const payloadType = requestData.payload.type
  if (!payloadType) {
    statusMessage.value = { type: 'error', text: 'Veuillez remplir les champs obligatoires.' }
    isSubmitting.value = false
    return
  }

  // Format the full request body expected by backend `RequestCreate`
  const requestBody = {
    type: payloadType, // e.g., 'IT_INCIDENT' or 'FACILITY_MAINTENANCE'
    priority: requestData.priority,
    description: requestData.description,
    category: requestData.category,
    project_id: requestData.project_id,
    payload: requestData.payload
  }

  try {
    // --- MOCKED API CALL ---
    console.log('Submitting to API /api/v1/requests', requestBody)
    await new Promise(resolve => setTimeout(resolve, 1500)) // Simulate network latency
    
    // Success
    statusMessage.value = { type: 'success', text: 'Votre demande a été soumise avec succès et est en attente de validation.' }
    
    // Reset form
    requestData.description = ''
    requestData.priority = 'NORMAL'
    requestData.payload = {}
    
  } catch (error) {
    console.error('Submission failed', error)
    statusMessage.value = { type: 'error', text: 'Une erreur est survenue lors de la soumission de votre demande.' }
  } finally {
    isSubmitting.value = false
    
    // Clear success message after 5 seconds
    if (statusMessage.value?.type === 'success') {
      setTimeout(() => {
        statusMessage.value = null
      }, 5000)
    }
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
