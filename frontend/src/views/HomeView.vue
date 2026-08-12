<script setup lang="ts">
import { ref, onMounted } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import MapLocationPicker from "@/components/project/MapLocationPicker.vue";
import api from '../services/api';
import { getStoredProfile } from '@/services/session';
import { useToast } from '@/composables/useToast';

const toast = useToast();

const kpis = ref([
  { title: "Projets Actifs", value: "0", icon: "work", color: "text-red-600", bg: "bg-red-50" },
  { title: "Employés", value: "0", icon: "people", color: "text-green-600", bg: "bg-green-50" },
  { title: "Demandes en attente", value: "0", icon: "assignment_late", color: "text-amber-600", bg: "bg-amber-50" },
  { title: "Alertes Stock", value: "0", icon: "warning", color: "text-red-600", bg: "bg-red-50" },
]);

const recentActivity = ref<any[]>([
  { id: 1, action: "Chargement des activités récentes...", time: "", icon: "sync" }
]);

const activeModal = ref<'project' | 'hr' | 'fuel' | null>(null);

const projectForm = ref({ code: '', nom: '', date_debut_estimee: '', date_fin_estimee: '', location: { lat: null, lng: null } });
const hrForm = ref({ employee_id: '', subject: '', leave_type: 'Congé', start_date: new Date().toISOString().split('T')[0], end_date: new Date().toISOString().split('T')[0], description: '' });
const fuelForm = ref({
  employee_id: '',
  request_date: new Date().toISOString().split('T')[0],
  affaire_no: '',
  dossier_no: '',
  vehicule_matricule: '',
  objet_deplacement: '',
  destination: '',
  releve_kilometrique: 0,
  nombre_jours: 1,
  quantite_carburant: 0,
});
const employees = ref<any[]>([]);
import { employeeService } from '@/services/employees';

const refreshDashboard = async () => {
  try {
    const kpiRes = await api.get('/dashboard/kpis');
    const data = kpiRes.data;
    if (kpis.value[0]) kpis.value[0].value = (data.active_projects || 0).toString();
    if (kpis.value[1]) kpis.value[1].value = (data.users || 0).toString();
    if (kpis.value[2]) kpis.value[2].value = (data.pending_requests || 0).toString();
    if (kpis.value[3]) kpis.value[3].value = (data.stock_alerts || 0).toString();
    
    const activityRes = await api.get('/dashboard/recent-activity');
    recentActivity.value = activityRes.data;
  } catch (error) {
    console.error("Failed to load dashboard data", error);
  }
};

const createProject = async () => {
  try {
    const payload: any = { ...projectForm.value };
    if (payload.location && payload.location.lat != null) {
      payload.latitude = payload.location.lat;
      payload.longitude = payload.location.lng;
    }
    delete payload.location;
    await api.post('/projects/', payload);
    toast.success("Projet créé avec succès");
    projectForm.value = { code: '', nom: '', date_debut_estimee: '', date_fin_estimee: '', location: { lat: null, lng: null } };
    activeModal.value = null;
    refreshDashboard();
  } catch (error) {
    toast.error("Erreur lors de la création du projet");
  }
};

const createHRRequest = async () => {
  try {
    await api.post('/requests/', {
      type: 'LEAVE',
      description: hrForm.value.description,
      payload: {
        employee_id: hrForm.value.employee_id,
        start_date: hrForm.value.start_date,
        end_date: hrForm.value.end_date,
        leave_type: hrForm.value.leave_type,
        reason: hrForm.value.subject
      }
    });
    activeModal.value = null;
    toast.success('Demande RH créée !');
    hrForm.value = { employee_id: '', subject: '', leave_type: 'Congé', start_date: new Date().toISOString().split('T')[0], end_date: new Date().toISOString().split('T')[0], description: '' };
    await refreshDashboard();
  } catch {
    toast.error('Erreur lors de la création de la demande RH.');
  }
};

const createFuelRequest = async () => {
  try {
    const payload = {
      type: 'FUEL',
      priority: 'NORMAL',
      category: 'Logistique',
      payload: {
        type: 'FUEL',
        employee_id: fuelForm.value.employee_id,
        vehicle_plate: fuelForm.value.vehicule_matricule,
        destination: fuelForm.value.destination,
        fuel_quantity: fuelForm.value.quantite_carburant,
        trip_days: fuelForm.value.nombre_jours,
        odometer_reading: fuelForm.value.releve_kilometrique,
        trip_purpose: fuelForm.value.objet_deplacement,
        affaire_no: fuelForm.value.affaire_no,
        dossier_no: fuelForm.value.dossier_no
      }
    };
    await api.post('/requests/', payload);
    activeModal.value = null;
    toast.success('Demande Carburant créée !');
    fuelForm.value = {
      employee_id: '',
      request_date: new Date().toISOString().split('T')[0],
      affaire_no: '',
      dossier_no: '',
      vehicule_matricule: '',
      objet_deplacement: '',
      destination: '',
      releve_kilometrique: 0,
      nombre_jours: 1,
      quantite_carburant: 0,
    };
    await refreshDashboard();
  } catch {
    toast.error('Erreur lors de la création de la demande carburant.');
  }
};

onMounted(async () => {
  await refreshDashboard();
  try {
    const empRes = await employeeService.getAllEmployees();
    employees.value = empRes.data;
  } catch (e) {
    console.error(e);
  }
});
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto space-y-8 w-full">
      
      <!-- Header -->
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Tableau de bord</h1>
          <p class="mt-1 text-gray-500">Aperçu général des activités COSELEC</p>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div v-for="kpi in kpis" :key="kpi.title" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-start gap-4">
          <div :class="[kpi.bg, kpi.color, 'p-3 rounded-lg']">
            <span class="material-symbols-outlined text-3xl">{{ kpi.icon }}</span>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-500">{{ kpi.title }}</p>
            <p class="text-2xl font-bold text-gray-900 mt-1">{{ kpi.value }}</p>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">Actions Rapides</h2>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <button @click="activeModal = 'project'" class="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <span class="material-symbols-outlined text-[#d10f2f] mb-2">add_circle</span>
            <span class="text-sm font-medium text-gray-700">Nouveau Projet</span>
          </button>
          <button @click="activeModal = 'hr'" class="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <span class="material-symbols-outlined text-[#d10f2f] mb-2">post_add</span>
            <span class="text-sm font-medium text-gray-700">Demande RH</span>
          </button>
          <router-link to="/stock/movement" class="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <span class="material-symbols-outlined text-[#d10f2f] mb-2">sync_alt</span>
            <span class="text-sm font-medium text-gray-700">Mouvement Stock</span>
          </router-link>
          <button @click="activeModal = 'fuel'" class="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
            <span class="material-symbols-outlined text-[#d10f2f] mb-2">directions_car</span>
            <span class="text-sm font-medium text-gray-700">Demande Carburant</span>
          </button>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Recent Activity -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-3">
          <h2 class="text-lg font-bold text-gray-900 mb-4">Activité Récente</h2>
          <ul class="space-y-4">
            <li v-for="act in recentActivity" :key="act.id" class="flex items-start gap-3">
              <div class="bg-gray-50 p-2 rounded-full mt-1">
                <span class="material-symbols-outlined text-sm text-gray-600">{{ act.icon }}</span>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-800">{{ act.action }}</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ act.time }}</p>
              </div>
            </li>
          </ul>
        </div>

      </div>


    </div>

    <!-- MODALS -->
    <div v-if="activeModal === 'project'" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-96 shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Nouveau Projet</h2>
        <form @submit.prevent="createProject" class="space-y-3">
          <input v-model="projectForm.code" placeholder="Code (ex: PRJ-01)" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
          <input v-model="projectForm.nom" placeholder="Nom du projet" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
          <div>
            <label class="block text-xs text-gray-500 mb-1">Date début estimée</label>
            <input type="date" v-model="projectForm.date_debut_estimee" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Date fin estimée</label>
            <input type="date" v-model="projectForm.date_fin_estimee" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Emplacement (Géolocalisation)</label>
            <MapLocationPicker v-model="projectForm.location" />
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <button type="button" @click="activeModal = null" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">Annuler</button>
            <button type="submit" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg">Créer</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="activeModal === 'hr'" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-xl w-96 shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-gray-900">Nouvelle Demande RH</h2>
        <form @submit.prevent="createHRRequest" class="space-y-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Collaborateur concerné</label>
            <select v-model="hrForm.employee_id" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500">
              <option value="" disabled>Sélectionner un collaborateur</option>
              <option v-for="emp in employees" :key="emp.id" :value="emp.id">
                {{ emp.first_name }} {{ emp.last_name }}
              </option>
            </select>
          </div>
          <input v-model="hrForm.subject" placeholder="Sujet / Raison" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
          <div class="grid grid-cols-2 gap-4">
            <select v-model="hrForm.leave_type" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500">
              <option value="Congé">Congé</option>
              <option value="Absence">Absence</option>
              <option value="Avance sur Salaire">Avance sur Salaire</option>
              <option value="Document">Document</option>
              <option value="Autre">Autre</option>
            </select>
            <div class="flex flex-col">
              <label class="text-xs text-gray-500">Date de début</label>
              <input type="date" v-model="hrForm.start_date" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            </div>
            <div class="flex flex-col">
              <label class="text-xs text-gray-500">Date de fin</label>
              <input type="date" v-model="hrForm.end_date" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500" />
            </div>
          </div>
          <textarea v-model="hrForm.description" placeholder="Description / Motif" rows="3" required class="border border-gray-300 px-3 py-2 w-full rounded-lg focus:outline-none focus:border-red-500"></textarea>
          <div class="flex justify-end gap-2 mt-4">
            <button type="button" @click="activeModal = null" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">Annuler</button>
            <button type="submit" class="bg-[#d10f2f] hover:bg-[#97091f] text-white px-4 py-2 rounded-lg">Soumettre</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="activeModal === 'fuel'" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 overflow-y-auto">
      <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl my-8">
        <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
          <h2 class="text-xl font-bold flex items-center gap-2">
            <span class="material-symbols-outlined">description</span>
            Nouvelle Demande de Carburant
          </h2>
          <button @click="activeModal = null" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <form @submit.prevent="createFuelRequest" class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Employé</label>
              <select v-model="fuelForm.employee_id" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                <option value="" disabled>Sélectionner un employé</option>
                <option v-for="emp in employees" :key="emp.id" :value="emp.id">
                  {{ emp.first_name }} {{ emp.last_name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input type="date" v-model="fuelForm.request_date" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">N° Affaire (Optionnel)</label>
              <input type="text" v-model="fuelForm.affaire_no" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">N° Dossier (Optionnel)</label>
              <input type="text" v-model="fuelForm.dossier_no" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Objet du Déplacement</label>
              <input type="text" v-model="fuelForm.objet_deplacement" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Matricule Véhicule</label>
              <input type="text" v-model="fuelForm.vehicule_matricule" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Destination</label>
              <input type="text" v-model="fuelForm.destination" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Relevé Kilométrique</label>
              <input type="number" v-model="fuelForm.releve_kilometrique" required min="1" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre de jours</label>
              <input type="number" v-model="fuelForm.nombre_jours" required min="1" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Quantité de carburant (Litres)</label>
              <input type="number" step="0.01" v-model="fuelForm.quantite_carburant" required min="0.01" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
          </div>
          <div class="mt-8 flex justify-end gap-3 pt-4 border-t">
            <button type="button" @click="activeModal = null" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">
              Annuler
            </button>
            <button type="submit" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition">
              Créer la demande
            </button>
          </div>
        </form>
      </div>
    </div>

  </AppLayout>
</template>