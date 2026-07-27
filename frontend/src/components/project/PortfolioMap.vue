<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <h2 class="text-xl font-bold text-gray-900 mb-4">Carte globale des Projets</h2>
    <div class="h-[500px] w-full rounded-lg overflow-hidden border border-gray-200 relative">
      <l-map ref="map" v-model:zoom="zoom" :center="center" :use-global-leaflet="false">
        <l-tile-layer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          layer-type="base"
          name="OpenStreetMap"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        ></l-tile-layer>
        
        <l-marker 
          v-for="project in validProjects" 
          :key="project.id" 
          :lat-lng="[project.latitude, project.longitude]"
        >
          <l-popup>
            <div class="p-1 min-w-[200px]">
              <div class="text-xs font-bold text-gray-500 mb-1">PROJET #{{ project.id }}</div>
              <div class="font-bold text-gray-900 text-base mb-1">{{ project.nom }}</div>
              <div class="text-sm text-gray-600 mb-3">
                <span v-if="project.client_name">Client: {{ project.client_name }}</span>
                <span v-else>Statut: {{ project.status }}</span>
              </div>
              <router-link 
                :to="`/projects/${project.id}`" 
                class="block w-full text-center bg-[#d10f2f] hover:bg-red-800 text-white text-sm font-medium py-1.5 px-3 rounded transition-colors"
              >
                Voir les détails
              </router-link>
            </div>
          </l-popup>
        </l-marker>
      </l-map>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import 'leaflet/dist/leaflet.css';
import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet';

const props = defineProps({
  projects: {
    type: Array,
    default: () => []
  }
});

// Centré sur Dakar
const center = ref([14.6928, -17.4467]);
const zoom = ref(11);

// Filtrer uniquement les projets avec des coordonnées valides
const validProjects = computed(() => {
  return props.projects.filter(p => p.latitude != null && p.longitude != null);
});
</script>

<style scoped>
/* Assure que la map ne dépasse pas sur les autres éléments de l'UI tels que les menus déroulants */
:deep(.leaflet-container) {
  z-index: 1;
}
/* Correction des icônes par défaut de Leaflet avec Vue 3 / Vite si nécessaire */
:deep(.leaflet-default-icon-path) {
  background-image: url('leaflet/dist/images/marker-icon.png');
}
</style>
