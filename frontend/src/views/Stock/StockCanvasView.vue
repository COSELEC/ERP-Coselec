<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { StockService } from '@/services/stock';
import AppLayout from '@/layouts/AppLayout.vue';
import { useToast } from '@/composables/useToast';

interface Category {
  id: number;
  code?: string;
  name: string;
  description?: string;
}

interface Product {
  id: number;
  code?: string;
  name: string;
  sku_code: string;
  category_id: number;
  safety_threshold: number;
}

interface CanvasBoard extends Category {
  items: Product[];
}

const isLoading = ref(false);
const errorMessage = ref('');
const toast = useToast();

const categories = ref<Category[]>([]);
const products = ref<Product[]>([]);

const showCategoryModal = ref(false);
const showProductModal = ref(false);
const openCategoryMenuId = ref<number | null>(null);
const openProductMenuId = ref<number | null>(null);

const catForm = reactive({ name: '', description: '' });
const prodForm = reactive({ name: '', sku_code: '', category_id: '', safety_threshold: 5 });

const fetchData = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const [catRes, prodRes] = await Promise.all([
      StockService.getCategories(),
      StockService.getProducts()
    ]);
    categories.value = (catRes.data || []).map((category: any) => ({
      id: Number(category.id),
      code: category.code,
      name: category.name,
      description: category.description
    }));

    products.value = (prodRes.data || []).map((product: any) => ({
      id: Number(product.id),
      code: product.code,
      name: product.name || product.designation,
      sku_code: product.sku_code || product.code,
      category_id: Number(product.category_id),
      safety_threshold: Number(product.safety_threshold ?? product.minimum_stock ?? 0)
    }));
  } catch {
    errorMessage.value = "Impossible de charger le catalogue. Vérifiez votre connexion et réessayez.";
  } finally {
    isLoading.value = false;
  }
};

const canvasBoards = computed<CanvasBoard[]>(() => {
  return categories.value.map(cat => ({
    ...cat,
    items: products.value.filter(p => p.category_id === cat.id)
  }));
});

const handleCreateCategory = async () => {
  if (!catForm.name) return;
  try {
    await StockService.createCategory({ ...catForm });
    catForm.name = ''; catForm.description = '';
    showCategoryModal.value = false;
    await fetchData();
    toast.success('Catégorie créée avec succès.');
  } catch { toast.error("Erreur lors de la création de la catégorie."); }
};

const openAddProduct = (catId: number) => {
  prodForm.category_id = catId.toString();
  showProductModal.value = true;
};

const handleCreateProduct = async () => {
  if (!prodForm.name || !prodForm.sku_code || !prodForm.category_id) return;
  try {
    await StockService.createProduct({
      name: prodForm.name,
      sku_code: prodForm.sku_code,
      category_id: Number(prodForm.category_id),
      safety_threshold: Number(prodForm.safety_threshold)
    });
    prodForm.name = ''; prodForm.sku_code = '';
    showProductModal.value = false;
    await fetchData();
    toast.success('Article ajouté au catalogue.');
  } catch { toast.error("Erreur lors de la création de l'article."); }
};

const handleEditCategory = async (category: Category) => {
  openCategoryMenuId.value = null;

  const newName = window.prompt('Nouveau nom de catégorie', category.name)?.trim();

  if (!newName || newName === category.name) {
    return;
  }

  try {
    await StockService.updateCategory(category.id, {
      name: newName,
      code: category.code
    });
    await fetchData();
    toast.success('Catégorie modifiée.');
  } catch {
    toast.error('Erreur lors de la modification de la catégorie.');
  }
};

const handleDeleteCategory = async (category: Category) => {
  openCategoryMenuId.value = null;

  const confirmed = window.confirm(`Supprimer la catégorie "${category.name}" ?`);

  if (!confirmed) {
    return;
  }

  try {
    await StockService.deleteCategory(category.id);
    await fetchData();
    toast.success('Catégorie supprimée.');
  } catch {
    toast.error('Impossible de supprimer la catégorie (elle contient peut-être des produits).');
  }
};

const handleEditProduct = async (product: Product) => {
  openProductMenuId.value = null;

  const newName = window.prompt("Nouvelle désignation de l'article", product.name)?.trim();
  if (!newName) {
    return;
  }

  const newSku = window.prompt('Nouveau SKU / Code', product.sku_code)?.trim();
  if (!newSku) {
    return;
  }

  const thresholdInput = window.prompt('Nouveau seuil de sécurité', String(product.safety_threshold));
  const thresholdNumber = Number(thresholdInput);

  if (!thresholdInput || Number.isNaN(thresholdNumber) || thresholdNumber < 0) {
    toast.error('Seuil invalide.');
    return;
  }

  try {
    await StockService.updateProduct(product.id, {
      name: newName,
      sku_code: newSku,
      category_id: product.category_id,
      safety_threshold: thresholdNumber
    });
    await fetchData();
    toast.success('Article modifié.');
  } catch {
    toast.error("Erreur lors de la modification de l'article.");
  }
};

const handleDeleteProduct = async (product: Product) => {
  openProductMenuId.value = null;

  const confirmed = window.confirm(`Supprimer l'article "${product.name}" ?`);

  if (!confirmed) {
    return;
  }

  try {
    await StockService.deleteProduct(product.id);
    await fetchData();
    toast.success('Article supprimé.');
  } catch {
    toast.error("Erreur lors de la suppression de l'article.");
  }
};

const toggleCategoryMenu = (categoryId: number) => {
  openProductMenuId.value = null;
  openCategoryMenuId.value = openCategoryMenuId.value === categoryId ? null : categoryId;
};

const toggleProductMenu = (productId: number) => {
  openCategoryMenuId.value = null;
  openProductMenuId.value = openProductMenuId.value === productId ? null : productId;
};

const closeMenus = () => {
  openCategoryMenuId.value = null;
  openProductMenuId.value = null;
};

const onDocumentClick = () => {
  closeMenus();
};

onMounted(() => {
  fetchData();
  document.addEventListener('click', onDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
});
</script>

<template>
  <AppLayout>
  <div class="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen font-sans">
    
    <!-- Top Action Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-gray-200 pb-5 mb-6 bg-white p-4 rounded-xl shadow-xs gap-4">
      <div class="flex items-center space-x-3">
        <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" />
        </svg>
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Canevas du Catalogue</h1>
          <p class="text-sm text-gray-500">Cartographie visuelle de vos matériels regroupés par famille d'article</p>
        </div>
      </div>

      <button @click="showCategoryModal = true" class="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2.5 rounded-xl transition-all shadow-md text-sm flex items-center space-x-2 self-start sm:self-center">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        <span>Nouvelle Catégorie</span>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-20 w-full">
      <div class="flex flex-col items-center gap-3">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-red-200 border-t-red-600"></div>
        <span class="text-sm text-gray-500 font-medium">Chargement du catalogue…</span>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="flex items-center justify-center py-20 w-full">
      <div class="flex flex-col items-center gap-4 text-center max-w-md">
        <span class="material-symbols-outlined text-4xl text-red-400">error_outline</span>
        <p class="text-sm text-red-600 font-medium">{{ errorMessage }}</p>
        <button @click="fetchData" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-colors">Réessayer</button>
      </div>
    </div>

    <!-- Canvas Scrollable Grid Workspace Board -->
    <div v-else class="flex space-x-6 overflow-x-auto pb-6 items-start snap-x scroll-smooth select-none">
      
      <!-- Category Kanban Column Board -->
      <div v-for="board in canvasBoards" :key="board.id" class="w-80 bg-white border border-gray-200 rounded-xl shadow-2xs flex-shrink-0 flex flex-col max-h-[75vh] snap-center">
        <!-- Header -->
        <div class="p-4 border-b border-gray-100 flex items-start justify-between bg-gray-50/50 rounded-t-xl">
          <div class="max-w-[80%]">
            <h3 class="font-bold text-gray-900 text-base truncate">{{ board.name }}</h3>
            <p class="text-xs text-gray-400 truncate mt-0.5" :title="board.description">{{ board.description || 'Aucune description' }}</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-gray-600 bg-gray-200 px-2.5 py-0.5 rounded-full whitespace-nowrap">
              {{ board.items.length }}
            </span>

            <div class="relative">
              <button
                type="button"
                @click.stop="toggleCategoryMenu(board.id)"
                class="cursor-pointer text-gray-500 hover:text-gray-700 p-1 rounded"
              >
                <span class="material-symbols-outlined text-base">more_vert</span>
              </button>
              <div
                v-if="openCategoryMenuId === board.id"
                @click.stop
                class="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1"
              >
                <button @click="handleEditCategory(board)" class="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  Modifier
                </button>
                <button @click="handleDeleteCategory(board)" class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50">
                  Supprimer
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Scrollable Product Cards Stack -->
        <div class="p-3 overflow-y-auto space-y-3 bg-gray-50/40 custom-scrollbar flex-1">
          <div v-for="product in board.items" :key="product.id" class="bg-white border border-gray-200 p-3 rounded-lg shadow-3xs hover:shadow-xs transition-shadow border-l-4 border-l-red-500">
            <div class="flex items-start justify-between gap-2">
              <div class="font-semibold text-gray-900 text-sm leading-snug">{{ product.name }}</div>
              <div class="relative">
                <button
                  type="button"
                  @click.stop="toggleProductMenu(product.id)"
                  class="list-none cursor-pointer text-gray-400 hover:text-gray-600 p-0.5 rounded"
                >
                  <span class="material-symbols-outlined text-base">more_vert</span>
                </button>
                <div
                  v-if="openProductMenuId === product.id"
                  @click.stop
                  class="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1"
                >
                  <button @click="handleEditProduct(product)" class="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                    Modifier
                  </button>
                  <button @click="handleDeleteProduct(product)" class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50">
                    Supprimer
                  </button>
                </div>
              </div>
            </div>
            <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100 text-xxs text-gray-400 font-medium">
              <span class="bg-gray-100 px-1.5 py-0.5 rounded font-mono uppercase tracking-wider">SKU: {{ product.sku_code }}</span>
              <span class="flex items-center text-gray-500">
                <svg class="w-3 h-3 mr-0.5 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Seuil: {{ product.safety_threshold }}
              </span>
            </div>
          </div>

          <!-- Empty Column Stack State -->
          <div v-if="board.items.length === 0" class="text-center py-8 text-gray-400 text-xs italic">
            Aucun produit dans cette famille
          </div>
        </div>

        <!-- Add Inline Card Trigger Button -->
        <button @click="openAddProduct(board.id)" class="w-full text-center py-2.5 text-xs font-semibold text-red-600 hover:text-red-700 bg-white hover:bg-gray-50 border-t border-gray-100 rounded-b-xl transition-colors flex items-center justify-center space-x-1">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <span>Ajouter un article</span>
        </button>
      </div>

      <!-- Empty Total Canvas State -->
      <div v-if="canvasBoards.length === 0" class="text-center w-full py-16 text-gray-400">
        <p class="text-base font-medium">Créez votre première catégorie pour initialiser le canevas matériel</p>
      </div>
    </div>

    <!-- MODAL 1: Create Category -->
    <div v-if="showCategoryModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="bg-white rounded-xl max-w-md w-full shadow-xl border border-gray-100 overflow-hidden">
        <div class="bg-red-600 px-5 py-4 text-white flex justify-between items-center">
          <h3 class="font-bold text-base">Nouvelle Famille de Matériel</h3>
          <button @click="showCategoryModal = false" class="text-white/80 hover:text-white">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <form @submit.prevent="handleCreateCategory" class="p-5 space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Nom de la catégorie *</label>
            <input type="text" v-model="catForm.name" required placeholder="Ex: Outillage, Luminaires..." class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Description / Notes</label>
            <textarea v-model="catForm.description" rows="2" placeholder="Détails optionnels sur l'usage..." class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500"></textarea>
          </div>
          <div class="flex justify-end space-x-3 pt-2">
            <button type="button" @click="showCategoryModal = false" class="px-4 py-2 border text-gray-600 rounded-lg text-sm font-semibold hover:bg-gray-50">Annuler</button>
            <button type="submit" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg text-sm shadow-xs">Créer la catégorie</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL 2: Create Product Card -->
    <div v-if="showProductModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="bg-white rounded-xl max-w-md w-full shadow-xl border border-gray-100 overflow-hidden">
        <div class="bg-red-600 px-5 py-4 text-white flex justify-between items-center">
          <h3 class="font-bold text-base">Ajouter un Article au Catalogue</h3>
          <button @click="showProductModal = false" class="text-white/80 hover:text-white">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <form @submit.prevent="handleCreateProduct" class="p-5 space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Désignation de l'article *</label>
            <input type="text" v-model="prodForm.name" required placeholder="Ex: Projecteur LED 50W IP65" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Code Article / SKU *</label>
            <input type="text" v-model="prodForm.sku_code" required placeholder="Ex: PRJ-LED-50W" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500" />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Seuil de sécurité (Alerte Alarme)</label>
            <input type="number" v-model.number="prodForm.safety_threshold" min="0" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-red-500" />
          </div>
          <div class="flex justify-end space-x-3 pt-2">
            <button type="button" @click="showProductModal = false" class="px-4 py-2 border text-gray-600 rounded-lg text-sm font-semibold hover:bg-gray-50">Annuler</button>
            <button type="submit" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg text-sm shadow-xs">Ajouter l'article</button>
          </div>
        </form>
      </div>
    </div>

  </div>
  </AppLayout>
</template>

<style scoped>
/* Scrolled workspace tweaks */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 9999px;
}
</style>