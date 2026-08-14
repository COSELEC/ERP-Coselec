<template>
  <AppLayout>
  <div class="max-w-7xl mx-auto font-sans">
    
    <!-- Header -->
    <div class="flex items-center space-x-3 border-b border-gray-200 pb-5 mb-6 bg-white p-4 rounded-xl shadow-xs">
      <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Mouvements de Stock</h1>
        <p class="text-sm text-gray-500">Suivi en temps réel des entrées et sorties de matériel</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <div class="flex flex-col items-center gap-3">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-red-200 border-t-red-600"></div>
        <span class="text-sm text-gray-500 font-medium">Chargement…</span>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="flex items-center justify-center py-20">
      <div class="flex flex-col items-center gap-4 text-center max-w-md">
        <span class="material-symbols-outlined text-4xl text-red-400">error_outline</span>
        <p class="text-sm text-red-600 font-medium">{{ errorMessage }}</p>
        <button @click="initPage" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-colors">Réessayer</button>
      </div>
    </div>

    <!-- Layout Split Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
      
      <!-- Form Container Card -->
      <div class="bg-white border border-gray-200 rounded-xl shadow-xs overflow-hidden">
        <div class="bg-red-600 px-5 py-4 text-white flex items-center space-x-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 class="font-bold text-sm uppercase tracking-wider">Nouvelle Opération</h2>
        </div>
        
        <form @submit.prevent="submitMovement" class="p-5 space-y-4">
          <!-- Flow Type Buttons -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Type de flux</label>
            <div class="grid grid-cols-2 gap-3">
              <button 
                type="button" 
                @click="form.type = 'ENTRY'"
                :class="form.type === 'ENTRY' ? 'bg-green-600 text-white font-semibold border-green-600 shadow-sm' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'"
                class="flex items-center justify-center space-x-2 border rounded-xl py-2.5 text-sm transition-all"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 4.5l-15 15m0 0h11.25m-11.25 0V8.25" />
                </svg>
                <span>Entrée</span>
              </button>
              <button 
                type="button" 
                @click="form.type = 'EXIT'"
                :class="form.type === 'EXIT' ? 'bg-red-600 text-white font-semibold border-red-600 shadow-sm' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'"
                class="flex items-center justify-center space-x-2 border rounded-xl py-2.5 text-sm transition-all"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                </svg>
                <span>Sortie</span>
              </button>
            </div>
          </div>

          <!-- Category Select (Parent Cascade) -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Famille / Catégorie</label>
            <select v-model="selectedCategoryId" required class="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-sm text-gray-800 focus:outline-none focus:border-red-500 cursor-pointer">
              <option value="" disabled>Sélectionner une catégorie...</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>

          <!-- Product Select (Child Cascade) -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Article / Matériel</label>
            <select v-model="form.product_id" :disabled="!selectedCategoryId" required class="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-sm text-gray-800 focus:outline-none focus:border-red-500 disabled:bg-gray-100 disabled:text-gray-400 cursor-pointer">
              <option value="" disabled>Choisir un article...</option>
              <option v-for="prod in products" :key="prod.id" :value="prod.id">
                {{ prod.designation }} {{ prod.code ? `(${prod.code})` : '' }}
              </option>
            </select>
          </div>

          <!-- Warehouse Target Select -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Entrepôt</label>
            <select v-model="form.warehouse_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-sm text-gray-800 focus:outline-none focus:border-red-500 cursor-pointer">
              <option value="" disabled>Choisir un emplacement...</option>
              <option v-for="wh in warehouses" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
            </select>
          </div>

          <!-- Entities / Ownership Toggle Group -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Entité Associée</label>
            <div class="flex items-center space-x-6 p-2 bg-gray-50 border border-gray-200 rounded-lg mb-2">
              <label class="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer font-medium">
                <input type="radio" :value="true" v-model="isInternalMovement" class="text-red-600 focus:ring-red-500" />
                <span>Interne (Coselec)</span>
              </label>
              <label class="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer font-medium">
                <input type="radio" :value="false" v-model="isInternalMovement" class="text-red-600 focus:ring-red-500" />
                <span>Entreprise Partenaire</span>
              </label>
            </div>

            <!-- Dynamic Partner Field Grid row -->
            <div v-if="!isInternalMovement">
              <select v-model="form.partner_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-sm text-gray-800 focus:outline-none focus:border-red-500 cursor-pointer">
                <option value="" disabled>Choisir l'entreprise partenaire...</option>
                <option v-for="part in displayedPartners" :key="part.id" :value="part.id">{{ part.name }}</option>
              </select>
            </div>
          </div>

          <!-- Quantities metric counter -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Quantité</label>
            <input type="number" v-model.number="form.quantity" min="1" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500" />
          </div>

          <!-- Notes documentation comments textarea -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Commentaire / Destination</label>
            <textarea v-model="form.notes" rows="2" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500 placeholder-gray-400" placeholder="Ex: Remplacement matériel défectueux..."></textarea>
          </div>

          <!-- Validation Submission Action Button -->
          <button type="submit" :disabled="isSubmitting" class="w-full bg-red-600 hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl transition-all shadow-md flex items-center justify-center space-x-2 mt-2">
            <div v-if="isSubmitting" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <span>{{ isSubmitting ? 'Enregistrement…' : 'Valider le mouvement' }}</span>
          </button>
        </form>
      </div>

      <!-- Right Column: History List -->
      <div class="lg:col-span-2 bg-white border border-gray-200 rounded-xl shadow-xs overflow-hidden">
        <div class="bg-gray-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 class="font-bold text-gray-800 text-base">Historique des Flux Récents</h2>
          </div>
          <span class="text-xs text-gray-600 bg-gray-200/70 px-3 py-1 rounded-full font-bold uppercase tracking-wider">
            {{ movements.length }} Flux
          </span>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase text-xs tracking-wider font-bold">
                <th @click="sortBy('type')" class="px-6 py-4 cursor-pointer hover:bg-gray-100 transition">
                  <div class="flex items-center gap-2">Type <span v-if="sortColumn === 'type'" class="material-symbols-outlined text-xs">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
                </th>
                <th @click="sortBy('product')" class="px-6 py-4 cursor-pointer hover:bg-gray-100 transition">
                  <div class="flex items-center gap-2">Article <span v-if="sortColumn === 'product'" class="material-symbols-outlined text-xs">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
                </th>
                <th @click="sortBy('warehouse')" class="px-6 py-4 cursor-pointer hover:bg-gray-100 transition">
                  <div class="flex items-center gap-2">Emplacement <span v-if="sortColumn === 'warehouse'" class="material-symbols-outlined text-xs">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
                </th>
                <th @click="sortBy('partner')" class="px-6 py-4 cursor-pointer hover:bg-gray-100 transition">
                  <div class="flex items-center gap-2">Propriétaire / Tiers <span v-if="sortColumn === 'partner'" class="material-symbols-outlined text-xs">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
                </th>
                <th @click="sortBy('quantity')" class="px-6 py-4 text-center cursor-pointer hover:bg-gray-100 transition">
                  <div class="flex items-center justify-center gap-2">Quantité <span v-if="sortColumn === 'quantity'" class="material-symbols-outlined text-xs">{{ sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward' }}</span></div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 text-sm text-gray-700">
              <tr v-for="item in sortedMovements" :key="item.id" class="hover:bg-gray-50/60 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                  <span 
                    :class="item.type === 'ENTRY' ? 'text-green-700 bg-green-50 border-green-200' : 'text-red-700 bg-red-50 border-red-200'" 
                    class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border space-x-1"
                  >
                    <svg v-if="item.type === 'ENTRY'" class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 4.5l-15 15m0 0h11.25m-11.25 0V8.25" />
                    </svg>
                    <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                    </svg>
                    <span>{{ item.type === 'ENTRY' ? 'Entrée' : 'Sortie' }}</span>
                  </span>
                </td>
                <td class="px-6 py-4 font-semibold text-gray-900 max-w-xs">
                  {{ resolveProductLabel(item) }}
                </td>
                <td class="px-6 py-4 text-gray-600">
                  {{ resolveWarehouseLabel(item) }}
                </td>
                <td class="px-6 py-4 text-gray-500 font-medium">
                  {{ item.partner?.name || 'Coselec Interne' }}
                </td>
                <td class="px-6 py-4 text-center font-bold text-base whitespace-nowrap">
                  <span :class="item.type === 'ENTRY' ? 'text-green-600' : 'text-red-600'">
                    {{ item.type === 'ENTRY' ? '+' : '-' }}{{ item.quantity }}
                  </span>
                </td>
              </tr>
              <tr v-if="movements.length === 0">
                <td colspan="5" class="px-6 py-12 text-center text-gray-400 font-medium">
                  Aucun mouvement enregistré sur votre base pour le moment.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { StockService } from '@/services/stock';
import AppLayout from '@/layouts/AppLayout.vue';
import { useToast, useTableSort } from '@/composables';
import axios from 'axios';

type MovementType = 'ENTRY' | 'EXIT';

interface Category {
  id: number;
  name: string;
}

interface Product {
  id: number;
  code: string;
  designation: string;
  category_id: number;
}

interface Warehouse {
  id: number;
  name: string;
}

interface Partner {
  id: number;
  code?: string;
  name: string;
}

interface Movement {
  id: number;
  product_id: number;
  warehouse_id: number;
  quantity: number;
  type: MovementType;
  product?: Product | null;
  warehouse?: Warehouse | null;
  partner?: Partner | null;
}

interface MovementForm {
  type: MovementType;
  product_id: string;
  warehouse_id: string;
  quantity: number;
  partner_id: string;
  notes: string;
}

// --- UI / UX State Control ---
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref('');
const isInternalMovement = ref(true); // Defaults to Coselec internal handling
const toast = useToast();

// --- Backend Data Stores ---
const categories = ref<Category[]>([]);
const products = ref<Product[]>([]);
const allProducts = ref<Product[]>([]);
const warehouses = ref<Warehouse[]>([]);
const partners = ref<Partner[]>([]);
const movements = ref<Movement[]>([]);

const { sortColumn, sortOrder, sortBy } = useTableSort(movements, '', 'asc');

const isInternalPartner = (partner: Partner | undefined) => {
  if (!partner) {
    return false;
  }

  const name = (partner.name || '').toLowerCase();
  const code = (partner.code || '').toLowerCase();

  return (
    name.includes('coselec') ||
    code.includes('coselec') ||
    code === 'internal' ||
    code === 'int'
  );
};

const displayedPartners = computed(() => {
  return partners.value.filter((partner) => !isInternalPartner(partner));
});

const productsById = computed(() => {
  const map = new Map<number, Product>();

  for (const product of allProducts.value) {
    map.set(product.id, product);
  }

  return map;
});

const warehousesById = computed(() => {
  const map = new Map<number, Warehouse>();

  for (const warehouse of warehouses.value) {
    map.set(warehouse.id, warehouse);
  }

  return map;
});

// --- Dynamic Cascading Selector Stores ---
const selectedCategoryId = ref('');

const getInternalPartnerId = () => {
  const internalPartner = partners.value.find((partner) => isInternalPartner(partner));

  return internalPartner?.id;
};

// --- Reactive Form Object Payload ---
const form = reactive<MovementForm>({
  type: 'ENTRY',
  product_id: '',
  warehouse_id: '',
  quantity: 1,
  partner_id: '',
  notes: ''
});

// --- Fetch App State Data Rows On Mount ---
const initPage = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const [catRes, prodRes, whRes, partRes, movRes] = await Promise.all([
      StockService.getCategories(),
      StockService.getProducts(),
      StockService.getWarehouses(),
      StockService.getPartners(),
      StockService.getMovements()
    ]);
    
    categories.value = catRes.data;
    allProducts.value = prodRes.data;
    warehouses.value = whRes.data;
    partners.value = partRes.data;
    movements.value = movRes.data;
  } catch {
    errorMessage.value = "Impossible de charger les données. Vérifiez votre connexion.";
  } finally {
    isLoading.value = false;
  }
};

// --- Watcher: Cascade selection logic (Category -> Products) ---
watch(selectedCategoryId, async (newCategoryId) => {
  form.product_id = ''; // Reset product selection on category change
  products.value = [];
  
  if (!newCategoryId) return;
  
  try {
    const prodRes = await StockService.getProducts(Number(newCategoryId));
    products.value = prodRes.data;
  } catch {
    toast.error("Erreur lors du chargement des produits.");
  }
});

// --- Watcher: Clean up partner assignments on toggling internal checkbox ---
watch(isInternalMovement, (isInternal) => {
  if (isInternal) {
    const internalPartnerId = getInternalPartnerId();
    form.partner_id = internalPartnerId ? String(internalPartnerId) : '';
  }
});

const resolveProductLabel = (movement: Movement) => {
  return (
    movement.product?.designation ||
    productsById.value.get(movement.product_id)?.designation ||
    `Produit #${movement.product_id}`
  );
};

const resolveWarehouseLabel = (movement: Movement) => {
  return (
    movement.warehouse?.name ||
    warehousesById.value.get(movement.warehouse_id)?.name ||
    `Entrepôt #${movement.warehouse_id}`
  );
};

const sortedMovements = computed(() => {
  if (!sortColumn.value) return movements.value;
  return [...movements.value].sort((a, b) => {
    let valA: any = '';
    let valB: any = '';

    if (sortColumn.value === 'type') {
      valA = a.type;
      valB = b.type;
    } else if (sortColumn.value === 'product') {
      valA = resolveProductLabel(a);
      valB = resolveProductLabel(b);
    } else if (sortColumn.value === 'warehouse') {
      valA = resolveWarehouseLabel(a);
      valB = resolveWarehouseLabel(b);
    } else if (sortColumn.value === 'partner') {
      valA = a.partner?.name || 'Coselec Interne';
      valB = b.partner?.name || 'Coselec Interne';
    } else if (sortColumn.value === 'quantity') {
      valA = a.quantity;
      valB = b.quantity;
    }

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

// --- Form Validation & Submission ---
const submitMovement = async () => {
  if (!form.product_id || !form.warehouse_id || form.quantity < 1) {
    toast.error("Veuillez remplir correctement tous les champs obligatoires.");
    return;
  }

  if (!isInternalMovement.value && !form.partner_id) {
    toast.error("Veuillez sélectionner une entreprise partenaire.");
    return;
  }

  const resolvedPartnerId = isInternalMovement.value
    ? (getInternalPartnerId() ?? null)
    : Number(form.partner_id);

  isSubmitting.value = true;
  try {
    const payload = {
      product_id: Number(form.product_id),
      warehouse_id: Number(form.warehouse_id),
      quantity: form.quantity,
      type: form.type,
      partner_id: resolvedPartnerId,
      notes: form.notes || undefined
    };

    await StockService.createMovement(payload);
    
    // Reset Form Fields (preserving defaults)
    form.notes = '';
    form.quantity = 1;
    form.product_id = '';
    selectedCategoryId.value = '';
    
    // Refresh Table
    const movRes = await StockService.getMovements();
    movements.value = movRes.data;
    
    toast.success("Le mouvement de stock a bien été enregistré !");
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const backendMessage =
        typeof error.response?.data?.detail === 'string'
          ? error.response.data.detail
          : "Impossible d'enregistrer l'opération.";
      toast.error(backendMessage);
      return;
    }

    toast.error("Impossible d'enregistrer l'opération.");
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(initPage);
</script>