<template>
  <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mt-4">
    <div class="flex justify-between items-center mb-6">
      <h3 class="text-xl font-bold text-gray-900">Stock du Projet</h3>
      <button @click="isTransferModalOpen = true" class="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 transition">
        Transférer depuis Magasin
      </button>
    </div>

    <div v-if="isLoading" class="text-gray-500 text-center py-4">Chargement...</div>
    <div v-else-if="stockItems.length === 0" class="text-gray-500 text-center py-4">Aucun stock alloué à ce projet.</div>
    <table v-else class="w-full text-left border-collapse">
      <thead>
        <tr class="border-b border-gray-200 bg-gray-50">
          <th class="py-3 px-4 font-semibold text-sm text-gray-700">Produit</th>
          <th class="py-3 px-4 font-semibold text-sm text-gray-700">Quantité</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in stockItems" :key="item.id" class="border-b border-gray-100 hover:bg-gray-50">
          <td class="py-3 px-4 text-sm font-medium text-gray-900">
             {{ getProductName(item.product_id) }}
          </td>
          <td class="py-3 px-4 text-sm">
             <span class="inline-block bg-red-100 text-red-800 rounded-full px-3 py-1 font-bold">{{ item.quantity }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="isTransferModalOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]">
      <div class="bg-white p-6 rounded-xl w-96 shadow-xl max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Transfert vers Projet</h2>
        <form @submit.prevent="submitTransfer" class="space-y-4">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1">Entrepôt Source</label>
            <select v-model="transferForm.from_warehouse_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2">
              <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1">Produit</label>
            <select v-model="transferForm.product_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2">
              <option v-for="p in products" :key="p.id" :value="p.id">{{ p.designation || p.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1">Quantité</label>
            <input type="number" v-model.number="transferForm.quantity" min="1" required class="w-full border border-gray-300 rounded-lg px-3 py-2" />
          </div>
          
          <div class="flex justify-end gap-2 mt-4">
            <button type="button" @click="isTransferModalOpen = false" class="px-4 py-2 border border-gray-300 rounded-lg">Annuler</button>
            <button type="submit" :disabled="isSubmitting" class="bg-red-600 text-white px-4 py-2 rounded-lg">
              {{ isSubmitting ? 'Transfert...' : 'Transférer' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { StockService } from '@/services/stock'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  projectId: number | null
}>()

const toast = useToast()
const isLoading = ref(false)
const isSubmitting = ref(false)
const stockItems = ref<any[]>([])
const products = ref<any[]>([])
const warehouses = ref<any[]>([])

const isTransferModalOpen = ref(false)
const transferForm = ref({
  product_id: '',
  from_warehouse_id: '',
  quantity: 1
})

const getProductName = (id: number) => {
  const p = products.value.find(prod => prod.id === id)
  return p ? (p.designation || p.name) : `Produit #${id}`
}

const loadData = async () => {
  if (!props.projectId) return
  isLoading.value = true
  try {
    const [stockRes, prodRes, whRes] = await Promise.all([
      StockService.getProjectStock(props.projectId),
      StockService.getProducts(),
      StockService.getWarehouses()
    ])
    stockItems.value = stockRes.data
    products.value = prodRes.data
    warehouses.value = whRes.data
  } catch (error) {
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

const submitTransfer = async () => {
  if (!props.projectId) return
  isSubmitting.value = true
  try {
    await api.post('/stock/transfer-to-project', {
      product_id: transferForm.value.product_id,
      from_warehouse_id: transferForm.value.from_warehouse_id,
      project_id: props.projectId,
      quantity: transferForm.value.quantity
    })
    toast.success("Transfert réussi")
    isTransferModalOpen.value = false
    await loadData() // Refresh stock
  } catch (error: any) {
    console.error(error)
    toast.error(error.response?.data?.detail || "Erreur lors du transfert")
  } finally {
    isSubmitting.value = false
  }
}

watch(() => props.projectId, () => {
  loadData()
})

onMounted(() => {
  loadData()
})
</script>
