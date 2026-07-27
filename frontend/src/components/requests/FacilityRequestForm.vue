<template>
  <form @submit.prevent="submitFacilityRequest" class="space-y-8">
    
    <!-- HEADER -->
    <div>
      <h2 class="text-2xl font-black tracking-tight text-gray-900">Nouvelle demande Facilities</h2>
      <p class="mt-2 text-sm text-gray-500">Sélectionnez la catégorie de votre besoin en logistique, matériel ou maintenance.</p>
    </div>

    <!-- MAIN CATEGORY SELECTION -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <label 
        class="group relative flex cursor-pointer rounded-3xl border-2 p-5 transition-all duration-300 ease-out hover:shadow-lg"
        :class="requestPayload.category === 'MAINTENANCE' ? 'border-red-600 bg-red-50/50 shadow-md' : 'border-gray-100 bg-white hover:border-red-200'"
      >
        <input type="radio" value="MAINTENANCE" v-model="requestPayload.category" class="sr-only" @change="resetFields" />
        <div class="flex flex-1 items-start gap-4">
          <div 
            class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl transition-colors duration-300"
            :class="requestPayload.category === 'MAINTENANCE' ? 'bg-red-600 text-white' : 'bg-red-100 text-red-600 group-hover:bg-red-200'"
          >
            <span class="material-symbols-outlined text-[24px]">build</span>
          </div>
          <div>
            <h3 class="text-base font-bold text-gray-900">Intervention / Réparation</h3>
            <p class="mt-1 text-xs font-medium text-gray-500 leading-relaxed">Problème de clim, électricité, aménagement, nettoyage, etc.</p>
          </div>
        </div>
        <div 
          class="absolute right-4 top-4 h-5 w-5 rounded-full border-2 transition-colors duration-300"
          :class="requestPayload.category === 'MAINTENANCE' ? 'border-5 border-red-600 bg-white' : 'border-gray-300'"
        ></div>
      </label>

      <label 
        class="group relative flex cursor-pointer rounded-3xl border-2 p-5 transition-all duration-300 ease-out hover:shadow-lg"
        :class="requestPayload.category === 'SUPPLIES' ? 'border-red-600 bg-red-50/50 shadow-md' : 'border-gray-100 bg-white hover:border-red-200'"
      >
        <input type="radio" value="SUPPLIES" v-model="requestPayload.category" class="sr-only" @change="resetFields" />
        <div class="flex flex-1 items-start gap-4">
          <div 
            class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl transition-colors duration-300"
            :class="requestPayload.category === 'SUPPLIES' ? 'bg-red-600 text-white' : 'bg-red-100 text-red-600 group-hover:bg-red-200'"
          >
            <span class="material-symbols-outlined text-[24px]">inventory_2</span>
          </div>
          <div>
            <h3 class="text-base font-bold text-gray-900">Matériel & Fournitures</h3>
            <p class="mt-1 text-xs font-medium text-gray-500 leading-relaxed">Demande de ramettes, stylos, outils, EPI ou retour matériel.</p>
          </div>
        </div>
        <div 
          class="absolute right-4 top-4 h-5 w-5 rounded-full border-2 transition-colors duration-300"
          :class="requestPayload.category === 'SUPPLIES' ? 'border-5 border-red-600 bg-white' : 'border-gray-300'"
        ></div>
      </label>
    </div>

    <!-- FORM FIELDS CONTAINER -->
    <div class="min-h-[300px]">
      <Transition 
        enter-active-class="transition duration-400 ease-out"
        enter-from-class="opacity-0 translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-300 ease-in absolute w-full"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-4"
      >
        <!-- MAINTENANCE FIELDS -->
        <div v-if="requestPayload.category === 'MAINTENANCE'" key="maintenance" class="space-y-5 rounded-2xl border border-gray-100 bg-gray-50 p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label class="mb-2 block text-sm font-semibold text-gray-700">Type de lieu</label>
              <select v-model="requestPayload.maintenance.location_type" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                <option value="bureau">En interne (Bureau / Siège)</option>
                <option value="chantier">Pour un projet (Chantier)</option>
              </select>
            </div>
            
            <div v-if="requestPayload.maintenance.location_type === 'chantier'">
              <label class="mb-2 block text-sm font-semibold text-gray-700">Projet concerné</label>
              <select v-model="requestPayload.maintenance.project_id" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                <option :value="null">-- Sélectionner le projet --</option>
                <option v-for="prj in projects" :key="prj.id" :value="prj.id">{{ prj.name }}</option>
              </select>
            </div>
            <div v-else>
              <label class="mb-2 block text-sm font-semibold text-gray-700">Bâtiment / Zone exacte</label>
              <input type="text" v-model="requestPayload.maintenance.building" placeholder="Ex: Bâtiment A, Salle de réunion 2" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" />
            </div>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Niveau d'urgence</label>
            <select v-model="requestPayload.maintenance.urgency" class="w-full md:w-1/2 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
              <option value="routine">Routine (Intervention normale)</option>
              <option value="urgent">Urgent (Gênant pour le travail)</option>
              <option value="emergency">Urgence absolue (Danger / Bloquant)</option>
            </select>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Description de l'intervention demandée</label>
            <textarea v-model="requestPayload.maintenance.description" required rows="4" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" placeholder="Décrivez le problème rencontré (ex: Fuite d'eau, Climatisation HS)..."></textarea>
          </div>
        </div>

        <!-- SUPPLIES FIELDS -->
        <div v-else-if="requestPayload.category === 'SUPPLIES'" key="supplies" class="space-y-5 rounded-2xl border border-gray-100 bg-gray-50 p-6">
          
          <div class="flex flex-col md:flex-row md:items-center justify-between bg-white p-4 rounded-xl border border-gray-200 gap-4">
            <div>
              <h4 class="text-sm font-bold text-gray-900">Type de demande</h4>
              <p class="text-xs text-gray-500 mt-1">S'agit-il d'une nouvelle demande ou d'un retour au magasin ?</p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium" :class="!requestPayload.supplies.is_return ? 'text-gray-900' : 'text-gray-400'">Demande</span>
              <button 
                type="button" 
                @click="requestPayload.supplies.is_return = !requestPayload.supplies.is_return"
                class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="requestPayload.supplies.is_return ? 'bg-amber-500' : 'bg-gray-200'"
              >
                <span class="sr-only">Type de demande</span>
                <span 
                  aria-hidden="true" 
                  class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="requestPayload.supplies.is_return ? 'translate-x-5' : 'translate-x-0'"
                />
              </button>
              <span class="text-sm font-medium" :class="requestPayload.supplies.is_return ? 'text-gray-900' : 'text-gray-400'">Retour</span>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label class="mb-2 block text-sm font-semibold text-gray-700">Demandeur / Responsable</label>
              <select v-model="requestPayload.employee_id" required class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                <option value="" disabled>Sélectionner un collaborateur</option>
                <option v-for="emp in employees" :key="emp.id" :value="emp.id">
                  {{ emp.first_name }} {{ emp.last_name }}
                </option>
              </select>
            </div>
            
            <div>
              <label class="mb-2 block text-sm font-semibold text-gray-700">Destination (Lieu / Projet)</label>
              <div class="flex flex-col gap-2">
                <select v-model="requestPayload.supplies.location_type" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                  <option value="bureau">En interne (Bureau / Siège)</option>
                  <option value="chantier">Pour un projet (Chantier)</option>
                </select>
                
                <select v-if="requestPayload.supplies.location_type === 'chantier'" v-model="requestPayload.supplies.project_id" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                  <option :value="null">-- Sélectionner le projet --</option>
                  <option v-for="prj in projects" :key="prj.id" :value="prj.id">{{ prj.name }}</option>
                </select>
              </div>
            </div>
          </div>
          
          <div class="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <label class="block text-sm font-semibold text-gray-700">Articles / Fournitures</label>
              <button type="button" @click="requestPayload.supplies.items.push({ category_id: null as any, product_id: null as any, designation: '', quantity: 1 })" class="text-red-600 hover:text-red-700 text-sm font-bold flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">add</span> Ajouter
              </button>
            </div>
            <div class="space-y-3">
              <div v-for="(item, idx) in requestPayload.supplies.items" :key="idx" class="flex items-center gap-3">
                <select v-model="item.category_id" class="w-1/3 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                  <option :value="null">-- Catégorie --</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                </select>
                
                <select v-model="item.product_id" required @change="updateDesignation(item)" class="flex-1 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
                  <option :value="null">-- Produit --</option>
                  <option v-for="prod in products.filter(p => !item.category_id || p.category_id === item.category_id)" :key="prod.id" :value="prod.id">{{ prod.designation }}</option>
                </select>
                
                <input v-model.number="item.quantity" required type="number" min="1" class="w-24 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" />
                <button v-if="requestPayload.supplies.items.length > 1" type="button" @click="requestPayload.supplies.items.splice(idx, 1)" class="text-red-500 hover:text-red-700 p-2">
                  <span class="material-symbols-outlined text-[20px]">delete</span>
                </button>
              </div>
            </div>
          </div>
          
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Justification du besoin</label>
            <textarea v-model="requestPayload.supplies.justification" required rows="3" class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" placeholder="Précisez l'usage prévu pour ce matériel..."></textarea>
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
  employee_id: '', // Demandeur
  category: '', // 'MAINTENANCE', 'SUPPLIES'
  maintenance: {
    location_type: 'bureau',
    project_id: null,
    building: '',
    urgency: 'routine',
    description: ''
  },
  supplies: {
    is_return: false,
    location_type: 'bureau',
    project_id: null,
    items: [{ category_id: null, product_id: null, designation: '', quantity: 1 }],
    justification: ''
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
  // Optionnel: nettoyer les champs quand on change de catégorie
}

const resetForm = () => {
  Object.assign(requestPayload, getInitialPayload())
}

const submitFacilityRequest = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;

  try {
    let payloadDetails = {};
    let backendRequestType = '';
    
    if (requestPayload.category === 'MAINTENANCE') {
      backendRequestType = 'FACILITY_MAINTENANCE';
      payloadDetails = {
        type: backendRequestType,
        location: requestPayload.maintenance.location_type === 'chantier' ? 'Chantier/Projet' : 'Bureau Interne',
        building: requestPayload.maintenance.building,
        urgency: requestPayload.maintenance.urgency,
        description: requestPayload.maintenance.description
      };
    } else if (requestPayload.category === 'SUPPLIES') {
      backendRequestType = 'FACILITY_SUPPLIES';
      payloadDetails = {
        type: backendRequestType,
        is_return: requestPayload.supplies.is_return,
        items: requestPayload.supplies.items,
        justification: requestPayload.supplies.justification,
        urgency: 'routine'
      };
    }

    const projectId = requestPayload.category === 'MAINTENANCE' 
      ? requestPayload.maintenance.project_id 
      : requestPayload.supplies.project_id;

    const finalPayload = {
      type: backendRequestType,
      priority: requestPayload.category === 'MAINTENANCE' && requestPayload.maintenance.urgency === 'emergency' ? 'URGENT' : 'NORMAL',
      description: requestPayload.category === 'MAINTENANCE' ? requestPayload.maintenance.description : requestPayload.supplies.justification,
      project_id: projectId,
      department_id: null,
      payload: payloadDetails
    };

    // Note: To submit 'on behalf of' employee_id, we'd add requester_id to the request wrapper, but API might derive it from token. 
    // If backend accepts it:
    if (requestPayload.employee_id) {
      (finalPayload.payload as any).target_employee_id = requestPayload.employee_id; // Store in payload
    }

    await api.post('/requests/', finalPayload);
    
    toast.success("Demande Facility envoyée avec succès.");
    resetForm();
    
  } catch (error) {
    console.error(error);
    toast.error("Erreur lors de l'envoi de la demande.");
  } finally {
    isSubmitting.value = false;
  }
}
</script>
