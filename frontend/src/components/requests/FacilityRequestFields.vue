<template>
  <div class="space-y-6">
    <!-- Type d'intervention -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Type d'intervention Facility</label>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <label 
          v-for="type in facilityTypes" 
          :key="type.value"
          class="relative flex items-center justify-center p-4 border rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
          :class="isTypeSelected(type.value) ? 'border-amber-500 bg-amber-50 ring-1 ring-amber-500' : 'border-gray-200'"
        >
          <input 
            type="radio" 
            :value="type.value" 
            v-model="interventionCategory" 
            class="sr-only"
            @change="updateType(type)"
          >
          <span class="text-sm font-medium text-gray-900 text-center">{{ type.label }}</span>
        </label>
      </div>
    </div>

    <div class="space-y-4 bg-gray-50 p-4 rounded-xl border border-gray-100">
      
      <!-- FOURNITURES (FACILITY_SUPPLIES) -->
      <template v-if="modelValue.type === 'FACILITY_SUPPLIES'">
        <div>
          <label class="block text-sm font-medium text-gray-700">Description de l'article</label>
          <input type="text" v-model="modelValue.item_description" placeholder="Ex: Ramettes de papier, Stylos..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm p-2 border" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Quantité</label>
          <input type="number" min="1" v-model.number="modelValue.quantity" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm p-2 border" />
        </div>
      </template>

      <!-- MAINTENANCE / SÉCURITÉ / AMÉNAGEMENT (FACILITY_MAINTENANCE) -->
      <template v-if="modelValue.type === 'FACILITY_MAINTENANCE'">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Localisation (Type)</label>
            <select v-model="modelValue.location" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm p-2 border">
              <option value="bureau">Bureau</option>
              <option value="entrepot">Entrepôt</option>
              <option value="chantier">Chantier spécifique</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Bâtiment / Zone exacte</label>
            <input type="text" v-model="modelValue.building" placeholder="Ex: Bâtiment A, Salle 3..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm p-2 border" />
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Description de la demande</label>
          <textarea 
            v-model="modelValue.description" 
            rows="3" 
            placeholder="Détaillez le besoin d'aménagement ou le problème de maintenance..."
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm p-2 border"
          ></textarea>
        </div>
      </template>

      <!-- Urgence (Commun aux payload Facility) -->
      <div>
        <label class="block text-sm font-medium text-gray-700">Urgence d'intervention</label>
        <select v-model="modelValue.urgency" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm p-2 border">
          <option value="routine">Routine</option>
          <option value="urgent">Urgent</option>
          <option value="emergency">Urgence absolue</option>
        </select>
      </div>

      <!-- Liaison Stock (Conditionnelle - Mockée pour le moment) -->
      <div class="pt-4 mt-2 border-t border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <h4 class="text-sm font-medium text-gray-900">Liaison Stock (Prévisionnel)</h4>
            <p class="text-xs text-gray-500">Imputer cette demande sur un stock spécifique ?</p>
          </div>
          <button 
            type="button" 
            @click="useStockLink = !useStockLink"
            class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            :class="useStockLink ? 'bg-amber-600' : 'bg-gray-200'"
          >
            <span class="sr-only">Utiliser liaison stock</span>
            <span 
              aria-hidden="true" 
              class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
              :class="useStockLink ? 'translate-x-5' : 'translate-x-0'"
            />
          </button>
        </div>

        <div v-if="useStockLink" class="mt-4 p-3 bg-amber-50/50 rounded-lg border border-amber-100 flex gap-4">
          <div class="flex-1">
            <label class="block text-xs font-medium text-gray-700">Type de stock</label>
            <select v-model="stockType" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-xs p-2 border">
              <option value="general">Stock Normal/Général</option>
              <option value="project">Stock Projet (Chantier)</option>
            </select>
          </div>
          <div class="flex-1" v-if="stockType === 'project'">
            <label class="block text-xs font-medium text-gray-700">Projet ciblé</label>
            <select disabled class="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 shadow-sm sm:text-xs p-2 border text-gray-500">
              <option>Projet Alpha (Mock)</option>
            </select>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const facilityTypes = [
  { value: 'maintenance', label: 'Maintenance', payloadType: 'FACILITY_MAINTENANCE' },
  { value: 'security', label: 'Sécurité/Électricité', payloadType: 'FACILITY_MAINTENANCE' },
  { value: 'layout', label: 'Aménagement', payloadType: 'FACILITY_MAINTENANCE' },
  { value: 'supplies', label: 'Fournitures', payloadType: 'FACILITY_SUPPLIES' }
]

const interventionCategory = ref('maintenance')
const useStockLink = ref(false)
const stockType = ref('general')

if (!props.modelValue.type) {
  emit('update:modelValue', { 
    type: 'FACILITY_MAINTENANCE',
    location: 'bureau',
    building: '',
    urgency: 'routine',
    description: ''
  })
}

const isTypeSelected = (val) => interventionCategory.value === val

const updateType = (selectedType) => {
  const base = { type: selectedType.payloadType }
  
  if (selectedType.payloadType === 'FACILITY_SUPPLIES') {
    emit('update:modelValue', { 
      ...base, 
      item_description: '', 
      quantity: 1, 
      urgency: 'routine' 
    })
  } else {
    emit('update:modelValue', { 
      ...base, 
      location: 'bureau', 
      building: '', 
      urgency: 'routine', 
      description: `[${selectedType.label}] ` 
    })
  }
}
</script>
