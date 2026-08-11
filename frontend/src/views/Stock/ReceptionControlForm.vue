<template>
  <AppLayout>
    <div class="p-6 max-w-4xl mx-auto">
      <div class="mb-6 border-b border-gray-200 pb-4">
        <h1 class="text-3xl font-bold text-gray-900">Formulaire de Contrôle de Réception</h1>
        <p class="text-sm text-gray-500 mt-1">Saisie des articles reçus suite à une commande fournisseur.</p>
      </div>

      <form @submit.prevent="submitReception" class="space-y-8 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Fournisseur</label>
            <select v-model="form.supplier_id" required class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
              <option value="" disabled>Sélectionner un fournisseur</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Réf. Bon de Commande (PO) Optionnel</label>
            <input type="number" v-model.number="form.po_id" placeholder="ID du PO" class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100" />
          </div>
          
          <div>
            <label class="mb-2 block text-sm font-semibold text-gray-700">Type de Stock</label>
            <select v-model="form.stock_type" required class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
              <option value="GENERAL">Général (Magasin)</option>
              <option value="PROJECT">Projet</option>
            </select>
          </div>
          
          <div v-if="form.stock_type === 'PROJECT'">
            <label class="mb-2 block text-sm font-semibold text-gray-700">Projet</label>
            <select v-model="form.project_id" required class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100">
              <option value="" disabled>Sélectionner un projet</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.nom }} ({{ p.code }})</option>
            </select>
          </div>
        </div>

        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="block text-sm font-semibold text-gray-700">Articles Réceptionnés</label>
            <button type="button" @click="addLine" class="text-red-600 hover:text-red-700 text-sm font-bold flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">add</span> Ajouter
            </button>
          </div>
          
          <div class="space-y-4">
            <div v-for="(line, index) in form.lines" :key="index" class="p-4 bg-gray-50 border border-gray-200 rounded-xl flex flex-wrap gap-4 items-end relative">
              <button v-if="form.lines.length > 1" type="button" @click="removeLine(index)" class="absolute -top-2 -right-2 bg-red-100 text-red-600 rounded-full p-1 hover:bg-red-200">
                <span class="material-symbols-outlined text-[14px]">close</span>
              </button>
              
              <div class="flex-1 min-w-[200px]">
                <label class="text-xs font-semibold text-gray-600">Désignation</label>
                <input v-model="line.designation" required type="text" class="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-400 focus:ring-2 focus:ring-red-100" />
              </div>
              <div class="w-24">
                <label class="text-xs font-semibold text-gray-600">Qté CMD</label>
                <input v-model.number="line.qty_ordered" type="number" min="0" class="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-400 focus:ring-2 focus:ring-red-100" />
              </div>
              <div class="w-24">
                <label class="text-xs font-semibold text-gray-600">Qté Livrée</label>
                <input v-model.number="line.qty_delivered" required type="number" min="0" class="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-400 focus:ring-2 focus:ring-red-100" />
              </div>
              <div class="w-24 flex flex-col items-center">
                <label class="text-xs font-semibold text-gray-600 mb-2">Conforme</label>
                <input v-model="line.is_compliant" type="checkbox" class="h-5 w-5 rounded border-gray-300 text-red-600 focus:ring-red-500" />
              </div>
              <div class="flex-1 min-w-[150px]">
                <label class="text-xs font-semibold text-gray-600">Remarques</label>
                <input v-model="line.notes" type="text" placeholder="Casse, erreur..." class="w-full mt-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-400 focus:ring-2 focus:ring-red-100" />
              </div>
            </div>
          </div>
        </div>
        
        <div class="pt-4 border-t border-gray-100 flex justify-end gap-3">
          <button type="submit" :disabled="isSubmitting" class="bg-red-600 text-white px-6 py-3 rounded-xl font-bold shadow-md shadow-red-200 hover:bg-red-700 flex items-center gap-2">
            <span v-if="isSubmitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
            <span v-else class="material-symbols-outlined text-[18px]">check_circle</span>
            Valider la réception
          </button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import AppLayout from '@/layouts/AppLayout.vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import { getStoredProfile } from '@/services/session'

const toast = useToast()
const isSubmitting = ref(false)
const suppliers = ref<any[]>([])
const projects = ref<any[]>([])
const currentEmployeeId = ref<number | null>(null)

const form = reactive({
  supplier_id: '',
  po_id: null as number | null,
  stock_type: 'GENERAL',
  project_id: '' as string | number,
  lines: [
    { product_id: null, designation: '', qty_ordered: 0, qty_delivered: 0, is_compliant: true, notes: '' }
  ]
})

onMounted(async () => {
  try {
    const res = await api.get('/partners/')
    suppliers.value = res.data
  } catch (e) {
    console.error(e)
  }
  
  try {
    const resProj = await api.get('/projects/')
    projects.value = resProj.data
  } catch (e) {
    console.error(e)
  }
  
  try {
    const profile = getStoredProfile()
    if (profile?.email) {
      const empRes = await api.get('/employees/', { params: { search: profile.email } })
      const match = empRes.data?.find((e: any) => e.email === profile.email)
      if (match) currentEmployeeId.value = match.id
    }
  } catch (e) {
    console.warn('Impossible de résoudre l\'employé connecté:', e)
  }
})

const addLine = () => {
  form.lines.push({ product_id: null, designation: '', qty_ordered: 0, qty_delivered: 0, is_compliant: true, notes: '' })
}

const removeLine = (index: number) => {
  form.lines.splice(index, 1)
}

const submitReception = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  
  try {
    const payload = {
      po_id: form.po_id,
      supplier_id: form.supplier_id,
      created_by: currentEmployeeId.value, 
      stock_type: form.stock_type,
      project_id: form.stock_type === 'PROJECT' ? form.project_id : null,
      lines: form.lines
    }
    
    await api.post('/receptions/', payload)
    toast.success("Contrôle de réception enregistré et PDF généré.")
    
    form.po_id = null
    form.supplier_id = ''
    form.stock_type = 'GENERAL'
    form.project_id = ''
    form.lines = [{ product_id: null, designation: '', qty_ordered: 0, qty_delivered: 0, is_compliant: true, notes: '' }]
    
  } catch (error) {
    console.error(error)
    toast.error("Erreur lors de l'enregistrement.")
  } finally {
    isSubmitting.value = false
  }
}
</script>
