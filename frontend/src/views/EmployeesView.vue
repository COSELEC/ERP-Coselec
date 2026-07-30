<template>
  <AppLayout>
    <div class="w-full flex flex-col relative h-full">
        <h1 class="text-2xl font-bold mb-4 text-[#b30c27] flex items-center gap-2">
          <span class="material-symbols-outlined">badge</span>
          <span>Gestion des employés</span>
        </h1>
        <button
          @click="showCreateModal = true"
          class="bg-[#d10f2f] w-max text-white px-4 py-2 rounded-xl hover:bg-[#97091f] shadow-[0_10px_30px_rgba(209,15,47,0.28)] transition flex items-center gap-2 mb-6"
        >
          <span class="material-symbols-outlined">person_add</span>
          <span>Ajouter un employé</span>
        </button>

        <div class="bg-white rounded-2xl shadow-[0_15px_40px_rgba(127,7,28,0.10)] border border-red-100 overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="bg-gradient-to-r from-red-100/90 to-red-50 text-left">
                <th @click="sortBy('matricule')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition">
                  <span class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-base">pin</span>
                    <span>Matricule</span>
                    <span v-if="sortColumn === 'matricule'" class="material-symbols-outlined text-sm">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span>
                  </span>
                </th>
                <th @click="sortBy('first_name')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition">
                  <span class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-base">person</span>
                    <span>Employé</span>
                    <span v-if="sortColumn === 'first_name'" class="material-symbols-outlined text-sm">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span>
                  </span>
                </th>
                <th @click="sortBy('email')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition">
                  <span class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-base">mail</span>
                    <span>Email</span>
                    <span v-if="sortColumn === 'email'" class="material-symbols-outlined text-sm">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span>
                  </span>
                </th>
                <th @click="sortBy('position')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition">
                  <span class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-base">work</span>
                    <span>Poste</span>
                    <span v-if="sortColumn === 'position'" class="material-symbols-outlined text-sm">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span>
                  </span>
                </th>
                <th @click="sortBy('status')" class="px-6 py-4 text-sm font-semibold text-[#7f071c] cursor-pointer hover:bg-red-50 transition">
                  <span class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-base">verified</span>
                    <span>Statut</span>
                    <span v-if="sortColumn === 'status'" class="material-symbols-outlined text-sm">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span>
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="employee in sortedEmployees"
                :key="employee.id"
                @click="openEmployeeDetails(employee)"
                class="border-t border-red-100/80 hover:bg-red-50/70 transition cursor-pointer"
              >
                <td class="px-6 py-4 text-gray-600 font-medium">
                  {{ employee.matricule || 'EMP' + String(employee.id).padStart(3, "0") }}
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-red-100 text-[#d10f2f] flex items-center justify-center font-semibold">
                      {{ employee.first_name[0] }}
                    </div>
                    <div>
                      <p class="font-medium text-gray-900">
                        {{ employee.first_name }} {{ employee.last_name }}
                      </p>
                      <p class="text-xs text-gray-500">
                        {{ employee.email }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 text-gray-500">{{ employee.email }}</td>
                <td class="px-6 py-4 text-gray-700">{{ employee.position }}</td>
                <td class="px-6 py-4">
                  <span :class="[getStatusClass(employee.status), 'px-3 py-1 rounded-full text-xs font-medium uppercase']">
                    {{ employee.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      <!-- Modal Nouvel Employé -->
      <div v-if="showCreateModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
        <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
          <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
            <h2 class="text-xl font-bold flex items-center gap-2">
              <span class="material-symbols-outlined">person_add</span>
              Nouvel Employé
            </h2>
            <button @click="showCreateModal = false" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          
          <form @submit.prevent="submitEmployee" class="p-6 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                <input 
                  type="text" 
                  v-model="form.first_name" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                <input 
                  type="text" 
                  v-model="form.last_name" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input 
                  type="email" 
                  v-model="form.email" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                <input 
                  type="text" 
                  v-model="form.phone" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Matricule</label>
                <input 
                  type="text" 
                  v-model="form.matricule" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Poste</label>
                <input 
                  type="text" 
                  v-model="form.position" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Département</label>
                <select 
                  v-model="form.department_id" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                >
                  <option value="" disabled>Sélectionner un département</option>
                  <option v-for="dep in departments" :key="dep.id" :value="dep.id">
                    {{ dep.name }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                <select 
                  v-model="form.status" 
                  required
                  class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                >
                  <option value="CDI">CDI</option>
                  <option value="CDD">CDD</option>
                  <option value="STAGIAIRE">Stagiaire</option>
                  <option value="PRESTATAIRE">Prestataire</option>
                  <option value="INACTIF">Inactif</option>
                </select>
              </div>
            </div>
            <div class="mt-8 flex justify-end gap-3 pt-4 border-t">
              <button type="button" @click="showCreateModal = false" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">
                Annuler
              </button>
              <button type="submit" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition">
                Créer
              </button>
            </div>
          </form>
        </div>
      </div>

      <div 
        v-if="isSlideOverOpen" 
        @click="closeSlideOver"
        class="fixed inset-0 bg-[#7f071c]/25 z-40 transition-opacity backdrop-blur-sm"
      ></div>

      <div 
        class="fixed inset-y-0 right-0 z-50 w-full max-w-3xl bg-gradient-to-b from-red-50 to-white shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col border-l border-red-100"
        :class="isSlideOverOpen ? 'translate-x-0' : 'translate-x-full'"
      >
        <div v-if="selectedEmployee" class="px-6 py-6 bg-white border-b border-red-100 flex justify-between items-start shadow-sm z-10">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-full bg-red-100 text-[#d10f2f] flex items-center justify-center text-xl font-bold">
              {{ selectedEmployee.first_name[0] }}{{ selectedEmployee.last_name[0] }}
            </div>
            <div>
              <h2 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <span class="material-symbols-outlined text-[#d10f2f]">account_circle</span>
                <span>{{ selectedEmployee.first_name }} {{ selectedEmployee.last_name }}</span>
              </h2>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-sm text-gray-500 font-medium">{{ selectedEmployee.position }}</span>
                <span class="text-gray-300">•</span>
                <span :class="[getStatusClass(selectedEmployee.status), 'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider']">
                  {{ selectedEmployee.status }}
                </span>
              </div>
            </div>
          </div>
          <button @click="closeSlideOver" class="p-2 text-[#b94a5d] hover:text-[#7f071c] hover:bg-red-100 rounded-full transition">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div v-if="selectedEmployee" class="flex-1 overflow-y-auto p-6 space-y-8">
          
          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">info</span>
              <span>Informations Générales</span>
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500 uppercase">Matricule</p>
                <p class="font-medium text-gray-900">{{ selectedEmployee.matricule || 'Non défini' }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 uppercase">Email professionnel</p>
                <p class="font-medium text-gray-900">{{ selectedEmployee.email }}</p>
              </div>
              </div>
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">contract</span>
              <span>Contrats</span>
            </h3>
            <EmployeeContracts :employeeId="selectedEmployee.id" />
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">folder_shared</span>
              <span>Documents</span>
            </h3>
            <EmployeeDocuments :employeeId="selectedEmployee.id" />
          </section>

            <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
              <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
                <span class="material-symbols-outlined text-base">event_available</span>
                <span>Congés</span>
              </h3>
              <EmployeeLeaves :employeeId="selectedEmployee.id" />
            </section>

            <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
              <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
                <span class="material-symbols-outlined text-base">business_center</span>
                <span>Projets Assignés</span>
              </h3>
              <EmployeeProjects :employeeId="selectedEmployee.id" />
            </section>
          </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import { employeeService } from "@/services/employees";
import { api } from "@/services/api";
import { useToast } from '@/composables/useToast';

const toast = useToast();

// IMPORT DE SOUS-COMPOSANTS
import EmployeeContracts from "@/components/employees/EmployeeContracts.vue";
import EmployeeDocuments from "@/components/employees/EmployeeDocuments.vue";
import EmployeeLeaves from "@/components/employees/EmployeeLeaves.vue";
import EmployeeProjects from "@/components/employees/EmployeeProjects.vue";

interface Employee {
  id: number;
  matricule: string;
  first_name: string;
  last_name: string;
  email: string;
  position: string;
  status: string;
}

const showCreateModal = ref(false);
const employees = ref<Employee[]>([]);
const departments = ref<any[]>([]);

// Sorting logic
const sortColumn = ref('');
const sortOrder = ref<'asc' | 'desc'>('asc');

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortOrder.value = 'asc';
  }
};

const sortedEmployees = computed(() => {
  if (!sortColumn.value) return employees.value;
  return [...employees.value].sort((a, b) => {
    let valA = (a as any)[sortColumn.value];
    let valB = (b as any)[sortColumn.value];

    if (valA === null || valA === undefined) valA = '';
    if (valB === null || valB === undefined) valB = '';

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  matricule: '',
  position: '',
  department_id: '',
  status: 'CDI'
});

async function submitEmployee() {
  try {
    const payload = {
      ...form.value,
      department_id: form.value.department_id ? Number(form.value.department_id) : null
    };
    await api.post('/employees/', payload);
    showCreateModal.value = false;
    // Reset form
    form.value = {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      matricule: '',
      position: '',
      department_id: '',
      status: 'CDI'
    };
    
    // Refresh list
    const response = await employeeService.getAllEmployees();
    employees.value = response.data;
  } catch (e) {
    console.error("Error creating employee", e);
    toast.error("Erreur lors de la création de l'employé");
  }
}

// --- GESTION DU VOLET LATÉRAL (SLIDE-OVER) ---
const isSlideOverOpen = ref(false);
const selectedEmployee = ref<Employee | null>(null);

const openEmployeeDetails = (employee: Employee) => {
  selectedEmployee.value = employee;
  // Petit délai optionnel pour la fluidité si beaucoup de données
  setTimeout(() => {
    isSlideOverOpen.value = true;
  }, 10);
};

const closeSlideOver = () => {
  isSlideOverOpen.value = false;
  // On attend la fin de l'animation CSS (300ms) pour vider l'employé
  setTimeout(() => {
    selectedEmployee.value = null;
  }, 300);
};
// ---------------------------------------------

const getStatusClass = (status: string) => {
  if (!status) return "bg-slate-100 text-slate-700";
  
  switch (status.toUpperCase()) {
    case "CDI":
    case "SUR SITE":
      return "bg-emerald-100 text-emerald-700";
    case "CDD":
    case "SUR CHANTIER":
    case "ALTERNANT":
      return "bg-amber-100 text-amber-700";
    case "STAGIAIRE":
      return "bg-sky-100 text-sky-700";
    case "EN CONGÉ":
    case "PRESTATAIRE":
      return "bg-violet-100 text-violet-700";
    case "INACTIF":
      return "bg-rose-100 text-rose-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
};

onMounted(async () => {
  try {
    const [empRes, depRes] = await Promise.all([
      employeeService.getAllEmployees(),
      api.get('/departments/')
    ]);
    employees.value = empRes.data;
    departments.value = depRes.data;
  } catch (e) {
    console.error("Error loading data", e);
  }
});
</script>