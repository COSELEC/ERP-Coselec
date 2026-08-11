<template>
  <div class="space-y-6">
    <!-- Type de besoin -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Type de besoin IT</label>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <label 
          v-for="type in itRequestTypes" 
          :key="type.value"
          class="relative flex items-center justify-center p-4 border rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
          :class="modelValue.type === type.value ? 'border-indigo-600 bg-indigo-50 ring-1 ring-indigo-600' : 'border-gray-200'"
        >
          <input 
            type="radio" 
            :value="type.value" 
            v-model="modelValue.type" 
            class="sr-only"
            @change="updateType"
          >
          <span class="text-sm font-medium text-gray-900">{{ type.label }}</span>
        </label>
      </div>
    </div>

    <!-- Champs conditionnels selon le type -->
    <div class="space-y-4 bg-gray-50 p-4 rounded-xl border border-gray-100">
      
      <!-- MATÉRIEL (IT_EQUIPMENT) -->
      <template v-if="modelValue.type === 'IT_EQUIPMENT'">
        <div>
          <label class="block text-sm font-medium text-gray-700">Type de matériel</label>
          <select v-model="modelValue.equipment_type" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
            <option value="laptop">PC Portable</option>
            <option value="desktop">PC Fixe</option>
            <option value="monitor">Écran / Périphérique</option>
            <option value="phone">Téléphone</option>
            <option value="other">Autre</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Spécifications (optionnel)</label>
          <input type="text" v-model="modelValue.specifications" placeholder="Ex: 16Go RAM, Clavier AZERTY..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border" />
        </div>
      </template>

      <!-- LOGICIEL / ACCÈS (IT_ACCESS) -->
      <template v-if="modelValue.type === 'IT_ACCESS'">
        <div>
          <label class="block text-sm font-medium text-gray-700">Nom du système / logiciel</label>
          <input type="text" v-model="modelValue.system_name" placeholder="Ex: AutoCAD, ERP, VPN..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Niveau d'accès</label>
          <select v-model="modelValue.access_level" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
            <option value="standard">Standard (Lecture/Écriture base)</option>
            <option value="admin">Administrateur</option>
          </select>
        </div>
      </template>

      <!-- SUPPORT / INCIDENT (IT_INCIDENT) -->
      <template v-if="modelValue.type === 'IT_INCIDENT'">
        <div>
          <label class="block text-sm font-medium text-gray-700">Système ou matériel affecté</label>
          <input type="text" v-model="modelValue.affected_system" placeholder="Tag équipement ou nom du logiciel..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Niveau d'impact</label>
          <select v-model="modelValue.impact_level" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
            <option value="low">Bas (Gênant mais non bloquant)</option>
            <option value="medium">Moyen (Impact sur certaines tâches)</option>
            <option value="high">Haut (Impact fort)</option>
            <option value="critical">Critique (Bloquant total)</option>
          </select>
        </div>
      </template>

      <!-- Description / Justification (Commun) -->
      <div>
        <label class="block text-sm font-medium text-gray-700">
          {{ modelValue.type === 'IT_INCIDENT' ? 'Description détaillée du problème' : 'Justification de la demande' }}
        </label>
        <textarea 
          v-model="sharedDescription" 
          rows="3" 
          placeholder="Décrivez votre besoin ou le problème rencontré..."
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
        ></textarea>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const itRequestTypes = [
  { value: 'IT_EQUIPMENT', label: 'Matériel' },
  { value: 'IT_ACCESS', label: 'Logiciel / Accès' },
  { value: 'IT_INCIDENT', label: 'Support Technique' }
]

if (!props.modelValue.type) {
  emit('update:modelValue', { 
    type: 'IT_INCIDENT',
    affected_system: '',
    impact_level: 'medium',
    error_message: ''
  })
}

const updateType = () => {
  const base = { type: props.modelValue.type }
  if (base.type === 'IT_EQUIPMENT') {
    emit('update:modelValue', { ...base, equipment_type: 'laptop', specifications: '', justification: props.modelValue.error_message || props.modelValue.justification || '' })
  } else if (base.type === 'IT_ACCESS') {
    emit('update:modelValue', { ...base, system_name: '', access_level: 'standard', justification: props.modelValue.error_message || props.modelValue.justification || '' })
  } else if (base.type === 'IT_INCIDENT') {
    emit('update:modelValue', { ...base, affected_system: '', impact_level: 'medium', error_message: props.modelValue.justification || props.modelValue.error_message || '' })
  }
}

const sharedDescription = computed({
  get() {
    return props.modelValue.type === 'IT_INCIDENT' ? props.modelValue.error_message : props.modelValue.justification
  },
  set(val) {
    if (props.modelValue.type === 'IT_INCIDENT') {
      props.modelValue.error_message = val
    } else {
      props.modelValue.justification = val
    }
    emit('update:modelValue', props.modelValue)
  }
})

</script>
