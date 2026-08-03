<template>
  <div class="map-location-picker">
    <!-- Search Bar -->
    <div class="mb-2 flex gap-2 relative z-[1000]">
      <input 
        type="text" 
        v-model="searchQuery" 
        @keydown.enter.prevent="searchLocation"
        placeholder="Rechercher une adresse..." 
        class="border border-gray-300 px-3 py-1.5 w-full rounded-md text-sm focus:outline-none focus:border-red-500"
      />
      <button 
        type="button" 
        @click="searchLocation" 
        class="bg-gray-100 border border-gray-300 px-3 py-1.5 rounded-md text-sm hover:bg-gray-200 transition-colors"
      >
        Chercher
      </button>
      <button 
        type="button" 
        @click="locateMe" 
        class="bg-red-50 border border-red-200 text-red-600 px-3 py-1.5 rounded-md text-sm hover:bg-red-100 transition-colors flex items-center"
        title="Ma position actuelle"
      >
        <span class="material-symbols-outlined text-[18px]">my_location</span>
      </button>

      <!-- Dropdown results -->
      <div v-if="searchResults.length > 0" class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
        <div 
          v-for="result in searchResults" 
          :key="result.place_id" 
          @click="selectResult(result)"
          class="px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
        >
          {{ result.display_name }}
        </div>
      </div>
    </div>

    <div style="height: 250px; width: 100%; border-radius: 0.5rem; overflow: hidden; border: 1px solid #e5e7eb; position: relative; z-index: 1;">
      <l-map
        ref="map"
        v-model:zoom="zoom"
        :center="center"
        @click="onMapClick"
      >
        <l-tile-layer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          layer-type="base"
          name="OpenStreetMap"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        ></l-tile-layer>

        <l-marker
          v-if="markerPosition"
          :lat-lng="markerPosition"
        ></l-marker>
      </l-map>
    </div>
    
    <div v-if="markerPosition" class="mt-2 text-sm text-gray-600 flex items-center justify-between">
      <div class="flex-1 truncate mr-2" :title="currentAddress">
        <strong>Adresse :</strong> {{ currentAddress || 'Sélectionnée manuellement' }}
        <span class="text-xs text-gray-400 ml-2">({{ markerPosition[0].toFixed(4) }}, {{ markerPosition[1].toFixed(4) }})</span>
      </div>
      <button 
        type="button" 
        @click="clearMarker"
        class="text-red-500 hover:text-red-700 text-xs font-semibold"
      >
        Effacer
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import 'leaflet/dist/leaflet.css';
import { LMap, LTileLayer, LMarker } from '@vue-leaflet/vue-leaflet';

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => null
  }
});

const emit = defineEmits(['update:modelValue']);

const defaultCenter = [14.6928, -17.4467];
const zoom = ref(12);
const center = ref(defaultCenter);
const markerPosition = ref(null);
const currentAddress = ref('');
const searchQuery = ref('');
const searchResults = ref([]);
const map = ref(null);

onMounted(() => {
  if (props.modelValue && props.modelValue.lat != null && props.modelValue.lng != null) {
    const initPos = [props.modelValue.lat, props.modelValue.lng];
    markerPosition.value = initPos;
    center.value = initPos;
    if (props.modelValue.address) {
      currentAddress.value = props.modelValue.address;
    }
  }

  // Fix Leaflet sizing issue in modals
  setTimeout(() => {
    if (map.value && map.value.leafletObject) {
      map.value.leafletObject.invalidateSize();
    }
  }, 300);
});

watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.lat != null && newVal.lng != null) {
    markerPosition.value = [newVal.lat, newVal.lng];
    center.value = [newVal.lat, newVal.lng];
    if (newVal.address) {
      currentAddress.value = newVal.address;
    } else {
        currentAddress.value = '';
    }
  } else {
    markerPosition.value = null;
    currentAddress.value = '';
  }
}, { deep: true });

const searchLocation = async () => {
  if (!searchQuery.value.trim()) return;
  
  try {
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery.value)}`);
    const data = await response.json();
    searchResults.value = data;
  } catch (error) {
    console.error("Geocoding error:", error);
  }
};

const locateMe = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const newPos = [lat, lng];
        markerPosition.value = newPos;
        center.value = newPos;
        zoom.value = 16;
        currentAddress.value = 'Localisation en cours...';
        emit('update:modelValue', { lat, lng, address: '' });
        reverseGeocode(lat, lng);
      },
      (error) => {
        console.error("Geolocation error:", error);
        switch(error.code) {
          case error.PERMISSION_DENIED:
            alert("L'accès à la géolocalisation a été refusé.\n\nVeuillez cliquer sur l'icône de cadenas à côté de l'URL dans votre navigateur (Chrome, Safari, Edge) et autoriser la 'Position' ou 'Localisation', puis réessayez.");
            break;
          case error.POSITION_UNAVAILABLE:
            alert("Les informations de localisation sont indisponibles.");
            break;
          case error.TIMEOUT:
            alert("La demande pour obtenir votre position a expiré.");
            break;
          default:
            alert("Une erreur s'est produite lors de la géolocalisation.");
            break;
        }
      }
    );
  } else {
    alert("La géolocalisation n'est pas supportée par votre navigateur.");
  }
};

const selectResult = (result) => {
  const lat = parseFloat(result.lat);
  const lon = parseFloat(result.lon);
  
  const newPos = [lat, lon];
  markerPosition.value = newPos;
  center.value = newPos;
  zoom.value = 16;
  
  currentAddress.value = result.display_name;
  searchResults.value = [];
  
  emit('update:modelValue', { lat: lat, lng: lon, address: result.display_name });
};

const reverseGeocode = async (lat, lng) => {
  try {
    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
    const data = await response.json();
    if (data && data.display_name) {
      currentAddress.value = data.display_name;
      emit('update:modelValue', { lat: lat, lng: lng, address: data.display_name });
    }
  } catch (error) {
    console.error("Reverse geocoding error:", error);
  }
};

const onMapClick = (e) => {
  const newPos = [e.latlng.lat, e.latlng.lng];
  markerPosition.value = newPos;
  currentAddress.value = '';
  emit('update:modelValue', { lat: e.latlng.lat, lng: e.latlng.lng, address: '' });
  
  reverseGeocode(e.latlng.lat, e.latlng.lng);
};

const clearMarker = () => {
  markerPosition.value = null;
  currentAddress.value = '';
  searchQuery.value = '';
  searchResults.value = [];
  emit('update:modelValue', { lat: null, lng: null, address: null });
};
</script>

<style scoped>
/* Leaflet fixes for broken marker images in Vue 3/Vite */
:deep(.leaflet-default-icon-path) {
  background-image: url('leaflet/dist/images/marker-icon.png');
}
</style>
