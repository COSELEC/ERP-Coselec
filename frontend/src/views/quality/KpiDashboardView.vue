<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import { kpiService, type KPIProcessus } from '@/services/kpi';
import { useToast } from '@/composables/useToast';
import KpiUploadModal from './KpiUploadModal.vue';
import KpiChartWidget from './KpiChartWidget.vue';

const toast = useToast();

const loading = ref(true);
const data = ref<KPIProcessus[]>([]);
const currentYear = ref(new Date().getFullYear());
const isUploadModalOpen = ref(false);

const selectedProcessus = ref<number | 'ALL'>('ALL');

const loadData = async () => {
  loading.value = true;
  try {
    data.value = await kpiService.getDashboardData(currentYear.value);
  } catch (error: any) {
    toast.error("Erreur lors du chargement des KPI");
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});

const changeYear = (delta: number) => {
  currentYear.value += delta;
  loadData();
};

const filteredData = computed(() => {
  if (selectedProcessus.value === 'ALL') return data.value;
  return data.value.filter(p => p.id === selectedProcessus.value);
});

const handleImported = () => {
  isUploadModalOpen.value = false;
  loadData();
};
</script>

<template>
  <AppLayout>
    <div class="h-full flex flex-col bg-gray-50/50">
      
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 px-8 py-6 flex-shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <span class="material-symbols-outlined text-[#d10f2f] text-3xl">insights</span>
            Suivi des KPI Qualité
          </h1>
          <p class="text-gray-500 mt-1 text-sm">Visualisation des indicateurs de performance</p>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- Year Selector -->
          <div class="flex items-center bg-gray-100 rounded-lg p-1">
            <button @click="changeYear(-1)" class="p-1 hover:bg-white rounded text-gray-600 shadow-sm transition-colors">
              <span class="material-symbols-outlined text-sm">chevron_left</span>
            </button>
            <span class="font-bold text-gray-900 px-4">{{ currentYear }}</span>
            <button @click="changeYear(1)" class="p-1 hover:bg-white rounded text-gray-600 shadow-sm transition-colors">
              <span class="material-symbols-outlined text-sm">chevron_right</span>
            </button>
          </div>

          <button 
            @click="isUploadModalOpen = true"
            class="flex items-center gap-2 bg-[#d10f2f] hover:bg-[#a80c26] text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            <span class="material-symbols-outlined text-sm">upload_file</span>
            Importer KPI (Excel)
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="px-8 py-4 bg-white border-b border-gray-100 flex items-center gap-4 flex-wrap shadow-sm z-10">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-gray-400 text-sm">filter_list</span>
          <span class="text-sm font-medium text-gray-700">Filtrer par Processus :</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button 
            @click="selectedProcessus = 'ALL'"
            class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors border"
            :class="selectedProcessus === 'ALL' ? 'bg-red-50 text-[#d10f2f] border-red-200' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          >
            Tous les processus
          </button>
          <button 
            v-for="proc in data" 
            :key="proc.id"
            @click="selectedProcessus = proc.id"
            class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors border"
            :class="selectedProcessus === proc.id ? 'bg-red-50 text-[#d10f2f] border-red-200' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          >
            {{ proc.name }}
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-8">
        <div v-if="loading" class="h-full flex justify-center items-center">
          <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-[#d10f2f]"></div>
        </div>
        
        <div v-else-if="filteredData.length === 0" class="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
          <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <span class="material-symbols-outlined text-3xl text-gray-400">monitoring</span>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">Aucune donnée pour {{ currentYear }}</h3>
          <p class="text-gray-500 mb-6">Il n'y a pas encore d'indicateurs de performance importés pour cette année, ou le processus sélectionné est vide.</p>
          <button 
            @click="isUploadModalOpen = true"
            class="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            Importer des données
          </button>
        </div>

        <div v-else class="space-y-8">
          <div v-for="processus in filteredData" :key="processus.id" class="space-y-4">
            <div class="flex items-center gap-2 border-b border-gray-200 pb-2">
              <h3 class="text-lg font-bold text-gray-900">{{ processus.name }}</h3>
              <span class="bg-gray-100 text-gray-600 text-xs font-semibold px-2 py-0.5 rounded-full">
                {{ processus.indicators.length }} indicateur(s)
              </span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <KpiChartWidget 
                v-for="ind in processus.indicators" 
                :key="ind.id"
                :indicator="ind"
                :year="currentYear"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <KpiUploadModal 
      v-if="isUploadModalOpen" 
      @close="isUploadModalOpen = false"
      @imported="handleImported"
    />
  </AppLayout>
</template>
