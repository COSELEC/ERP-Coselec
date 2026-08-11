<template>
  <form @submit.prevent="submitITRequest" class="space-y-6">
    


    <!-- Category Selection -->
    <div>
      <label class="mb-2 block text-sm font-semibold text-gray-700">Catégorie de la demande</label>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        
        <label 
          class="relative flex flex-col p-5 cursor-pointer rounded-2xl border-2 transition-all duration-200"
          :class="requestPayload.category === 'INCIDENT' ? 'border-red-500 bg-red-50 shadow-md transform scale-[1.02]' : 'border-gray-100 bg-white hover:border-red-200 hover:bg-red-50/30'"
        >
          <input type="radio" value="INCIDENT" v-model="requestPayload.category" @change="resetFields" class="sr-only">
          <span class="font-bold text-gray-900" :class="requestPayload.category === 'INCIDENT' ? 'text-red-700' : ''">Incident / Fix</span>
          <span class="text-xs mt-1 text-gray-500">Matériel ou logiciel en panne.</span>
        </label>

        <label 
          class="relative flex flex-col p-5 cursor-pointer rounded-2xl border-2 transition-all duration-200"
          :class="requestPayload.category === 'HARDWARE' ? 'border-red-500 bg-red-50 shadow-md transform scale-[1.02]' : 'border-gray-100 bg-white hover:border-red-200 hover:bg-red-50/30'"
        >
          <input type="radio" value="HARDWARE" v-model="requestPayload.category" @change="resetFields" class="sr-only">
          <span class="font-bold text-gray-900" :class="requestPayload.category === 'HARDWARE' ? 'text-red-700' : ''">Matériel</span>
          <span class="text-xs mt-1 text-gray-500">Besoin d'un nouvel équipement.</span>
        </label>

        <label 
          class="relative flex flex-col p-5 cursor-pointer rounded-2xl border-2 transition-all duration-200"
          :class="requestPayload.category === 'SOFTWARE' ? 'border-red-500 bg-red-50 shadow-md transform scale-[1.02]' : 'border-gray-100 bg-white hover:border-red-200 hover:bg-red-50/30'"
        >
          <input type="radio" value="SOFTWARE" v-model="requestPayload.category" @change="resetFields" class="sr-only">
          <span class="font-bold text-gray-900" :class="requestPayload.category === 'SOFTWARE' ? 'text-red-700' : ''">Accès & Logiciels</span>
          <span class="text-xs mt-1 text-gray-500">Droits, licences ou accès VPN.</span>
        </label>

      </div>
    </div>

    <!-- Dynamic Fields Area -->
    <div class="relative mt-2">
      <Transition name="slide-fade" mode="out-in">
        
        <!-- INCIDENT FIELDS -->
        <div v-if="requestPayload.category === 'INCIDENT'" key="incident" class="space-y-5 rounded-2xl border border-gray-100 bg-gray-50 p-6">
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Équipement ou logiciel concerné</label>
            <input type="text" v-model="requestPayload.incident.equipment_id" required placeholder="Ex: PC-042 ou AutoCAD" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" />
          </div>
          
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Niveau d'impact</label>
            <select v-model="requestPayload.incident.impact_level" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
              <option value="blocking">Bloquant tout mon travail</option>
              <option value="annoying">Gênant mais je peux travailler</option>
              <option value="minor">Mineur / Cosmétique</option>
            </select>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Reproduction du problème</label>
            <textarea v-model="requestPayload.incident.reproduction_steps" required rows="4" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" placeholder="Que faisiez-vous quand l'erreur s'est produite ?"></textarea>
          </div>
        </div>

        <!-- HARDWARE FIELDS -->
        <div v-else-if="requestPayload.category === 'HARDWARE'" key="hardware" class="space-y-5 rounded-2xl border border-gray-100 bg-gray-50 p-6">
          
          <div class="flex items-center justify-between bg-white p-4 rounded-xl border border-gray-200">
            <div>
              <h4 class="text-sm font-bold text-gray-900">Type de demande</h4>
              <p class="text-xs text-gray-500 mt-1">S'agit-il d'une nouvelle demande ou d'un retour de matériel ?</p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium" :class="!requestPayload.hardware.is_return ? 'text-gray-900' : 'text-gray-400'">Demande</span>
              <button 
                type="button" 
                @click="requestPayload.hardware.is_return = !requestPayload.hardware.is_return"
                class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="requestPayload.hardware.is_return ? 'bg-amber-500' : 'bg-gray-200'"
              >
                <span class="sr-only">Type de demande</span>
                <span 
                  aria-hidden="true" 
                  class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="requestPayload.hardware.is_return ? 'translate-x-5' : 'translate-x-0'"
                />
              </button>
              <span class="text-sm font-medium" :class="requestPayload.hardware.is_return ? 'text-gray-900' : 'text-gray-400'">Retour</span>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-5">
            <div>
              <label class="mb-2 block text-sm font-semibold text-gray-700">Lien avec un projet (Optionnel)</label>
              <select v-model="requestPayload.hardware.project_id" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                <option :value="null">-- Sélectionner le projet --</option>
                <option v-for="prj in projects" :key="prj.id" :value="prj.id">{{ prj.name }}</option>
              </select>
            </div>
          </div>
          
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="block text-sm font-semibold text-gray-700">Articles</label>
              <button type="button" @click="requestPayload.hardware.items.push({ category_id: null as any, product_id: null as any, designation: '', quantity: 1 })" class="text-red-600 hover:text-red-700 text-sm font-bold flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">add</span> Ajouter
              </button>
            </div>
            <div class="space-y-3">
              <div v-for="(item, idx) in requestPayload.hardware.items" :key="idx" class="flex items-center gap-3">
                <select v-model="item.category_id" class="w-1/3 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                  <option :value="null">-- Catégorie --</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                </select>
                
                <select v-model="item.product_id" required @change="updateDesignation(item)" class="flex-1 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                  <option :value="null">-- Produit --</option>
                  <option v-for="prod in products.filter(p => !item.category_id || p.category_id === item.category_id)" :key="prod.id" :value="prod.id">{{ prod.designation }}</option>
                </select>
                
                <input v-model.number="item.quantity" required type="number" min="1" class="w-24 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" />
                <button v-if="requestPayload.hardware.items.length > 1" type="button" @click="requestPayload.hardware.items.splice(idx, 1)" class="text-red-500 hover:text-red-700 p-2">
                  <span class="material-symbols-outlined text-[20px]">delete</span>
                </button>
              </div>
            </div>
          </div>
          
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Justification du besoin</label>
            <textarea v-model="requestPayload.hardware.justification" required rows="4" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" placeholder="Expliquez pourquoi vous avez besoin de ce matériel..."></textarea>
          </div>
        </div>

        <!-- SOFTWARE FIELDS -->
        <div v-else-if="requestPayload.category === 'SOFTWARE'" key="software" class="space-y-5 rounded-2xl border border-gray-100 bg-gray-50 p-6">
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Type d'accès demandé</label>
            <select v-model="requestPayload.software.access_type" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
              <option value="erp_account">Création de compte ERP</option>
              <option value="software_license">Licence logicielle spécifique</option>
              <option value="vpn">Accès VPN Distant</option>
              <option value="file_share">Accès Partage de fichiers (NAS)</option>
            </select>
          </div>

          <div class="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-bold text-gray-900">Accès temporaire</h4>
                <p class="text-xs text-gray-500 mt-1">Stagiaire, prestataire, besoin ponctuel ?</p>
              </div>
              <button 
                type="button" 
                @click="requestPayload.software.is_temporary = !requestPayload.software.is_temporary"
                class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="requestPayload.software.is_temporary ? 'bg-red-600' : 'bg-gray-200'"
              >
                <span class="sr-only">Accès temporaire</span>
                <span 
                  aria-hidden="true" 
                  class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="requestPayload.software.is_temporary ? 'translate-x-5' : 'translate-x-0'"
                />
              </button>
            </div>

            <div v-if="requestPayload.software.is_temporary" class="mt-4 pt-4 border-t border-gray-100">
              <label class="mb-2 block text-sm font-semibold text-gray-700">Date de fin d'accès</label>
              <input type="date" v-model="requestPayload.software.end_date" required class="w-full md:w-1/2 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" />
            </div>
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-else key="empty" class="rounded-2xl border border-dashed border-gray-300 py-12 px-6 flex items-center justify-center">
          <p class="text-gray-500 text-sm font-medium text-center">
            Veuillez sélectionner une catégorie pour afficher les détails.
          </p>
        </div>
      </Transition>
    </div>

    <!-- Footer / Actions -->
    <div class="flex flex-wrap items-center gap-3 pt-4">
      <button 
        type="submit" 
        :disabled="isSubmitting || !requestPayload.category"
        class="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-red-200 transition hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg v-if="isSubmitting" class="animate-spin -ml-1 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span v-else class="material-symbols-outlined text-[18px]">send</span>
        {{ isSubmitting ? "Envoi en cours..." : "Envoyer la demande" }}
      </button>
      
      <button 
        type="button" 
        @click="resetForm"
        class="inline-flex items-center gap-2 rounded-2xl border border-red-100 bg-white px-5 py-3 text-sm font-semibold text-red-700 transition hover:bg-red-50"
      >
        Réinitialiser
      </button>
    </div>

  </form>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { employeeService } from '@/services/employees'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'

const toast = useToast()
const isSubmitting = ref(false)
const employees = ref<any[]>([])
const projects = ref<any[]>([])
const categories = ref<any[]>([])
const products = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await employeeService.getAllEmployees()
    employees.value = res.data
  } catch (error) {
    console.error("Error loading employees", error)
  }
  try {
    const res = await api.get('/projects/')
    projects.value = res.data
  } catch (error) {
    console.error("Error loading projects", error)
  }
  try {
    const resCat = await api.get('/categories/')
    categories.value = resCat.data
    const resProd = await api.get('/products/')
    products.value = resProd.data
  } catch (error) {
    console.error("Error loading stock", error)
  }
})

const getInitialPayload = () => ({
  category: '', // 'INCIDENT', 'HARDWARE', 'SOFTWARE'
  incident: {
    equipment_id: '',
    impact_level: 'blocking',
    reproduction_steps: ''
  },
  hardware: {
    is_return: false,
    project_id: null,
    items: [{ category_id: null, product_id: null, designation: '', quantity: 1 }],
    justification: ''
  },
  software: {
    access_type: 'erp_account',
    is_temporary: false,
    end_date: ''
  }
})

const requestPayload = reactive(getInitialPayload())

const updateDesignation = (item: any) => {
  const prod = products.value.find(p => p.id === item.product_id);
  if(prod) {
    item.designation = prod.designation;
  }
}

const resetFields = () => {
  // Optionnel: nettoyer les autres champs quand on change de catégorie
}

const resetForm = () => {
  Object.assign(requestPayload, getInitialPayload())
}

const submitITRequest = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;

  try {
    let payloadDetails = {};
    let backendRequestType = '';
    
    // On mappe nos catégories frontend aux RequestType du backend
    if (requestPayload.category === 'INCIDENT') {
      backendRequestType = 'IT_INCIDENT';
      payloadDetails = {
        type: backendRequestType,
        affected_system: requestPayload.incident.equipment_id,
        error_message: requestPayload.incident.reproduction_steps,
        impact_level: requestPayload.incident.impact_level
      };
    } else if (requestPayload.category === 'HARDWARE') {
      backendRequestType = 'IT_EQUIPMENT';
      payloadDetails = {
        type: backendRequestType,
        is_return: requestPayload.hardware.is_return,
        items: requestPayload.hardware.items,
        justification: requestPayload.hardware.justification
      };
    } else if (requestPayload.category === 'SOFTWARE') {
      backendRequestType = 'IT_ACCESS';
      if (requestPayload.software.is_temporary && !requestPayload.software.end_date) {
        throw new Error("Veuillez renseigner la date de fin pour un accès temporaire.");
      }
      payloadDetails = {
        type: backendRequestType,
        system_name: requestPayload.software.access_type,
        access_level: 'standard',
        justification: requestPayload.software.is_temporary ? `Temporaire jusqu'au ${requestPayload.software.end_date}` : 'Permanent'
      };
    }

    const projectId = requestPayload.category === 'HARDWARE' ? requestPayload.hardware.project_id : null;

    await api.post('/requests/', {
      type: backendRequestType,
      priority: requestPayload.category === 'INCIDENT' ? 'HIGH' : 'NORMAL',
      description: requestPayload.category === 'INCIDENT' ? requestPayload.incident.reproduction_steps : (requestPayload.category === 'HARDWARE' ? requestPayload.hardware.justification : 'Demande d\'accès logiciel'),
      project_id: projectId,
      payload: {
        ...payloadDetails
      }
    });

    toast.success("Demande IT envoyée avec succès.");
    setTimeout(() => {
      resetForm();
    }, 1000);

  } catch (error: any) {
    console.error("Erreur de soumission :", error);
    toast.error(error.message || "Impossible de créer la demande.");
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
</style>
