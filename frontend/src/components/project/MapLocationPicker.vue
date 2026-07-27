<template>
  <div class="map-location-picker">
    <div style="height: 250px; width: 100%; border-radius: 0.5rem; overflow: hidden; border: 1px solid #e5e7eb;">
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
      <div>
        <strong>Latitude :</strong> {{ markerPosition[0].toFixed(6) }}, 
        <strong>Longitude :</strong> {{ markerPosition[1].toFixed(6) }}
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

// Dakar coordinates by default
const defaultCenter = [14.6928, -17.4467];
const zoom = ref(12);
const center = ref(defaultCenter);
const markerPosition = ref(null);

onMounted(() => {
  if (props.modelValue && props.modelValue.lat != null && props.modelValue.lng != null) {
    const initPos = [props.modelValue.lat, props.modelValue.lng];
    markerPosition.value = initPos;
    center.value = initPos;
  }
});

watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.lat != null && newVal.lng != null) {
    markerPosition.value = [newVal.lat, newVal.lng];
    center.value = [newVal.lat, newVal.lng];
  } else {
    markerPosition.value = null;
  }
}, { deep: true });

const onMapClick = (e) => {
  const newPos = [e.latlng.lat, e.latlng.lng];
  markerPosition.value = newPos;
  emit('update:modelValue', { lat: e.latlng.lat, lng: e.latlng.lng });
};

const clearMarker = () => {
  markerPosition.value = null;
  emit('update:modelValue', { lat: null, lng: null });
};
</script>

<style scoped>
/* Leaflet fixes for broken marker images in Vue 3/Vite */
:deep(.leaflet-default-icon-path) {
  background-image: url('leaflet/dist/images/marker-icon.png');
}
</style>
