<template>
  <AppLayout>
    <div class="p-6 max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Matrice des Stocks (Inventaire Croisé)</h1>
          <p class="text-sm text-gray-500 mt-1">Aperçu du matériel réparti sur les différents projets.</p>
        </div>
        
        <button 
          @click="exportInventorySheet"
          class="inline-flex items-center gap-2 bg-red-600 text-white px-5 py-2.5 rounded-lg hover:bg-red-700 transition font-medium shadow-sm"
        >
          <span class="material-symbols-outlined text-[20px]">download</span>
          Exporter Fiche d'Inventaire
        </button>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        
        <div v-if="loading" class="p-12 text-center text-gray-500">
          Chargement de la matrice...
        </div>
        
        <div v-else-if="matrixData.rows.length === 0" class="p-12 text-center text-gray-500">
          Aucune donnée disponible.
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm text-left">
            <thead class="bg-gray-50 text-gray-700 border-b border-gray-200">
              <tr>
                <th class="px-4 py-3 font-semibold sticky left-0 bg-gray-50 z-10 border-r border-gray-200 min-w-[200px]">
                  Produit
                </th>
                <th v-for="col in matrixData.columns" :key="col.id" class="px-4 py-3 font-semibold text-center whitespace-nowrap min-w-[120px]">
                  {{ col.name }}
                </th>
                <th class="px-4 py-3 font-bold text-red-600 bg-red-50 text-center sticky right-0 z-10">
                  TOTAL
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="row in matrixData.rows" :key="row.product_id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white border-r border-gray-200">
                  <div class="font-bold">{{ row.product_code }}</div>
                  <div class="text-xs text-gray-500">{{ row.product_name }}</div>
                </td>
                
                <td v-for="col in matrixData.columns" :key="col.id" class="px-4 py-3 text-center">
                  <span v-if="row.projects[col.id] > 0" class="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-gray-800 bg-gray-100 rounded-full">
                    {{ row.projects[col.id] }}
                  </span>
                  <span v-else class="text-gray-300">-</span>
                </td>
                
                <td class="px-4 py-3 text-center font-bold text-red-600 bg-red-50/30 sticky right-0">
                  {{ row.total_expected }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/layouts/AppLayout.vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const loading = ref(true)

const matrixData = ref({
  columns: [] as any[],
  rows: [] as any[]
})

const fetchMatrix = async () => {
  try {
    loading.value = true
    const res = await api.get('/matrix/')
    matrixData.value = res.data
  } catch (err) {
    console.error(err)
    toast.error("Erreur lors du chargement de la matrice.")
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMatrix()
})

const exportInventorySheet = () => {
  // Export en CSV simple : Produit | Qté Attendue | Qté Réelle
  let csvContent = "data:text/csv;charset=utf-8,";
  csvContent += "Code Produit,Designation,Qte Attendue (Systeme),Qte Reelle (Saisie)\r\n";
  
  matrixData.value.rows.forEach(row => {
    let code = `"${row.product_code || ''}"`;
    let name = `"${row.product_name || ''}"`;
    csvContent += `${code},${name},${row.total_expected},\r\n`;
  });
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `Fiche_Inventaire_${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  toast.success("Fiche d'inventaire téléchargée.");
}
</script>
