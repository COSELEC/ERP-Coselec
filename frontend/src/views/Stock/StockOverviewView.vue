<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue';
import { StockService } from '@/services/stock';
import AppLayout from '@/layouts/AppLayout.vue';

interface Category {
  id: number;
  name: string;
}

interface Warehouse {
  id: number;
  code?: string;
  name: string;
}

interface Partner {
  id: number;
  code?: string;
  name: string;
}

interface Product {
  id: number;
  code?: string;
  designation?: string;
  name?: string;
  sku_code?: string;
  category_id?: number;
}

interface StockItem {
  id: number;
  product_id: number;
  warehouse_id: number | null;
  partner_id: number | null;
  quantity: number;
}

interface QuantityCell {
  key?: string;
  id: number;
  name: string;
  qty: number;
}

interface StructuredInventoryItem {
  name: string;
  sku: string;
  magasinQty: number;
  localWhQuantities: QuantityCell[];
  partnerWhQuantities: QuantityCell[];
}

type SortDirection = 'asc' | 'desc';

const isLoading = ref(false);
const errorMessage = ref('');
const searchQuery = ref('');
const tableScrollRef = ref<HTMLDivElement | null>(null);
const tableElementRef = ref<HTMLTableElement | null>(null);
const sortKey = ref<string>('name');
const sortDirection = ref<SortDirection>('asc');
const miniScrollPosition = ref(0);
const miniScrollMax = ref(0);
let tableResizeObserver: ResizeObserver | null = null;

const tableMinWidth = computed(() => {
  const fixedColumnsWidth = 230 + 110;
  const warehouseColumnsWidth = displayedWarehouses.value.length * 150;
  const partnerColumnsWidth = partnerWarehouseColumns.value.length * 170;
  const safetyPadding = 40;

  return fixedColumnsWidth + warehouseColumnsWidth + partnerColumnsWidth + safetyPadding;
});

const enforcedTableMinWidth = computed(() => {
  return Math.max(tableMinWidth.value, 1100);
});

// Data stores
const categories = ref<Category[]>([]);
const products = ref<Product[]>([]);
const warehouses = ref<Warehouse[]>([]);
const partners = ref<Partner[]>([]);
const inventoryRaw = ref<StockItem[]>([]);

const productsById = computed(() => {
  const map = new Map<number, Product>();
  for (const product of products.value) {
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

const magasinWarehouseId = computed<number | null>(() => {
  const magasinWarehouse = warehouses.value.find((warehouse) => {
    const code = (warehouse.code || '').trim().toUpperCase();
    const name = (warehouse.name || '').trim().toLowerCase();

    return code === 'MAG' || name === 'magasin';
  });

  return magasinWarehouse?.id ?? null;
});

const displayedWarehouses = computed(() => {
  const magasinId = magasinWarehouseId.value;

  return warehouses.value.filter((warehouse) => warehouse.id !== magasinId);
});

const isInternalPartner = (partner: Partner | undefined) => {
  if (!partner) {
    return false;
  }

  const code = (partner.code || '').trim().toLowerCase();
  const name = (partner.name || '').trim().toLowerCase();

  return (
    name.includes('coselec') ||
    code.includes('coselec') ||
    code === 'internal' ||
    code === 'int'
  );
};

const internalPartnerIds = computed(() => {
  return new Set(
    partners.value
      .filter((partner) => isInternalPartner(partner))
      .map((partner) => partner.id)
  );
});

const displayedPartners = computed(() => {
  return partners.value.filter((partner) => !isInternalPartner(partner));
});

const partnerWarehouseColumns = computed(() => {
  const seen = new Set<string>();
  const columns: Array<{
    key: string;
    partnerId: number;
    partnerName: string;
    warehouseId: number;
    warehouseName: string;
  }> = [];

  for (const item of inventoryRaw.value) {
    if (item.partner_id === null || item.warehouse_id === null || item.quantity <= 0) {
      continue;
    }

    const partner = displayedPartners.value.find((entry) => entry.id === item.partner_id);
    if (!partner) {
      continue;
    }

    const warehouse = warehousesById.value.get(item.warehouse_id);
    if (!warehouse) {
      continue;
    }

    const key = `${partner.id}-${warehouse.id}`;
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    columns.push({
      key,
      partnerId: partner.id,
      partnerName: partner.name,
      warehouseId: warehouse.id,
      warehouseName: warehouse.name
    });
  }

  return columns.sort((a, b) => {
    const partnerCompare = a.partnerName.localeCompare(b.partnerName);
    if (partnerCompare !== 0) {
      return partnerCompare;
    }
    return a.warehouseName.localeCompare(b.warehouseName);
  });
});

const toggleSort = (key: string) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
    return;
  }

  sortKey.value = key;
  sortDirection.value = 'asc';
};

const getSortIcon = (key: string) => {
  if (sortKey.value !== key) {
    return 'unfold_more';
  }

  return sortDirection.value === 'asc' ? 'arrow_upward' : 'arrow_downward';
};

const getRowSortValue = (row: StructuredInventoryItem, key: string): number | string => {
  if (key === 'name') {
    return row.name;
  }

  if (key === 'sku') {
    return row.sku;
  }

  if (key === 'magasin') {
    return row.magasinQty;
  }

  if (key.startsWith('wh:')) {
    const warehouseId = Number(key.split(':')[1]);
    return row.localWhQuantities.find((entry) => entry.id === warehouseId)?.qty || 0;
  }

  if (key.startsWith('pt:')) {
    const columnKey = key.replace('pt:', '');
    return row.partnerWhQuantities.find((entry) => entry.key === columnKey)?.qty || 0;
  }

  return row.name;
};

const scrollTableHorizontally = (direction: 'left' | 'right') => {
  if (!tableScrollRef.value) {
    return;
  }

  tableScrollRef.value.scrollBy({
    left: direction === 'right' ? 360 : -360,
    behavior: 'smooth'
  });
};

const syncMiniScrollMetrics = () => {
  if (!tableScrollRef.value) {
    miniScrollMax.value = 0;
    miniScrollPosition.value = 0;
    return;
  }

  const max = Math.max(0, tableScrollRef.value.scrollWidth - tableScrollRef.value.clientWidth);
  miniScrollMax.value = max;
  miniScrollPosition.value = Math.min(tableScrollRef.value.scrollLeft, max);
};

const handleTableScroll = () => {
  if (!tableScrollRef.value) {
    return;
  }

  miniScrollPosition.value = tableScrollRef.value.scrollLeft;
};

const handleMiniScrollInput = () => {
  if (!tableScrollRef.value) {
    return;
  }

  tableScrollRef.value.scrollLeft = miniScrollPosition.value;
};

const setupTableScrollSync = async () => {
  await nextTick();
  syncMiniScrollMetrics();

  if (tableScrollRef.value) {
    tableScrollRef.value.addEventListener('scroll', handleTableScroll);
  }

  if (typeof ResizeObserver !== 'undefined') {
    tableResizeObserver = new ResizeObserver(() => {
      syncMiniScrollMetrics();
    });

    if (tableScrollRef.value) {
      tableResizeObserver.observe(tableScrollRef.value);
    }

    if (tableElementRef.value) {
      tableResizeObserver.observe(tableElementRef.value);
    }
  }

  window.addEventListener('resize', syncMiniScrollMetrics);
};

const syncTableScrollSoon = async () => {
  await nextTick();
  syncMiniScrollMetrics();
};

const initOverview = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const [catRes, prodRes, whRes, partRes, stockRes] = await Promise.all([
      StockService.getCategories(),
      StockService.getProducts(),
      StockService.getWarehouses(),
      StockService.getPartners(),
      StockService.getStockOverview()
    ]);
    
    categories.value = catRes.data;
    products.value = prodRes.data;
    warehouses.value = whRes.data;
    partners.value = partRes.data;
    inventoryRaw.value = stockRes.data;
  } catch {
    errorMessage.value = "Impossible de charger les données de stock. Vérifiez votre connexion et réessayez.";
  } finally {
    isLoading.value = false;
  }
};

const getMagasinQty = (productId: number) => {
  const magasinId = magasinWarehouseId.value;
  const internalIds = internalPartnerIds.value;

  const directMagasinQty = inventoryRaw.value
    .filter((item) => {
      return item.product_id === productId && item.warehouse_id === magasinId;
    })
    .reduce((sum, item) => sum + item.quantity, 0);

  if (directMagasinQty > 0) {
    return directMagasinQty;
  }

  return inventoryRaw.value
    .filter((item) => {
      return (
        item.product_id === productId &&
        item.partner_id !== null &&
        internalIds.has(item.partner_id)
      );
    })
    .reduce((sum, item) => sum + item.quantity, 0);
};

const getWarehouseQty = (productId: number, warehouseId: number) => {
  const internalIds = internalPartnerIds.value;

  return inventoryRaw.value
    .filter((item) => {
      if (item.product_id !== productId || item.warehouse_id !== warehouseId) {
        return false;
      }

      if (item.partner_id === null) {
        return true;
      }

      return internalIds.has(item.partner_id);
    })
    .reduce((sum, item) => sum + item.quantity, 0);
};

// Unique products row matrix builder
const structuredInventory = computed<StructuredInventoryItem[]>(() => {
  const uniqueProductIds = [...new Set(inventoryRaw.value.map(item => item.product_id))];
  
  return uniqueProductIds.map((productId) => {
    const product = productsById.value.get(productId);
    const productName = product?.designation || product?.name || `Produit #${productId}`;
    const productSku = product?.code || product?.sku_code || 'N/A';

    return {
      name: productName,
      sku: productSku,
      // Computes column metrics dynamically
      magasinQty: getMagasinQty(productId),
      localWhQuantities: displayedWarehouses.value.map(wh => ({
        id: wh.id,
        name: wh.name,
        qty: getWarehouseQty(productId, wh.id)
      })),
      partnerWhQuantities: partnerWarehouseColumns.value.map((column) => ({
        key: column.key,
        id: column.partnerId,
        name: `${column.partnerName} - ${column.warehouseName}`,
        qty: inventoryRaw.value
          .filter((item) => {
            return (
              item.product_id === productId &&
              item.partner_id === column.partnerId &&
              item.warehouse_id === column.warehouseId
            );
          })
          .reduce((sum, item) => sum + item.quantity, 0)
      }))
    };
  }).filter(item => {
    return item.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
           item.sku.toLowerCase().includes(searchQuery.value.toLowerCase());
  });
});

const sortedInventory = computed<StructuredInventoryItem[]>(() => {
  const rows = [...structuredInventory.value];

  rows.sort((a, b) => {
    const aValue = getRowSortValue(a, sortKey.value);
    const bValue = getRowSortValue(b, sortKey.value);

    const multiplier = sortDirection.value === 'asc' ? 1 : -1;

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return (aValue - bValue) * multiplier;
    }

    return String(aValue).localeCompare(String(bValue), 'fr', { sensitivity: 'base' }) * multiplier;
  });

  return rows;
});

onMounted(async () => {
  await initOverview();
  await setupTableScrollSync();
});

watch(
  [
    tableMinWidth,
    () => structuredInventory.value.length,
    () => displayedWarehouses.value.length,
    () => partnerWarehouseColumns.value.length,
    searchQuery
  ],
  () => {
    void syncTableScrollSoon();
  }
);

onBeforeUnmount(() => {
  if (tableScrollRef.value) {
    tableScrollRef.value.removeEventListener('scroll', handleTableScroll);
  }

  if (tableResizeObserver) {
    tableResizeObserver.disconnect();
    tableResizeObserver = null;
  }

  window.removeEventListener('resize', syncMiniScrollMetrics);
});
</script>

<template>
  <AppLayout>
  <div class="mx-auto flex h-full min-h-0 min-w-0 w-full max-w-full flex-col overflow-hidden font-sans">
    
    <!-- Top Header -->
    <div class="mb-6 flex shrink-0 flex-col gap-4 rounded-xl border-b border-gray-200 bg-white p-4 pb-5 shadow-xs">
      <div class="flex items-center space-x-3">
        <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
        <div class="min-w-0">
          <h1 class="text-2xl font-bold text-gray-900">État Global des Stocks</h1>
          <p class="text-sm text-gray-500">Visualisation matricielle des volumes par emplacement et par entité partenaire</p>

          <RouterLink
            to="/stock/movement"
            class="inline-flex items-center gap-2 mt-3 text-sm font-semibold text-[#d10f2f] hover:text-[#97091f]"
          >
            <span class="material-symbols-outlined text-base">sync_alt</span>
            <span>Accéder aux mouvements de stock</span>
          </RouterLink>
        </div>
        
      </div>
      
      <!-- Live Filter Input -->
      <div class="relative w-full md:max-w-md">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Rechercher un article, SKU..." 
          class="w-full border border-gray-300 rounded-lg pl-3 pr-4 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-1 items-center justify-center py-20">
      <div class="flex flex-col items-center gap-3">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-red-200 border-t-red-600"></div>
        <span class="text-sm text-gray-500 font-medium">Chargement des stocks…</span>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="flex flex-1 items-center justify-center py-20">
      <div class="flex flex-col items-center gap-4 text-center max-w-md">
        <span class="material-symbols-outlined text-4xl text-red-400">error_outline</span>
        <p class="text-sm text-red-600 font-medium">{{ errorMessage }}</p>
        <button @click="initOverview" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-colors">Réessayer</button>
      </div>
    </div>

    <!-- Big Matrix Overview Card -->
    <div v-else class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-red-100 bg-white shadow-xs">
      <div ref="tableScrollRef" class="stock-table-scroll min-h-0 flex-1 overflow-x-auto overflow-y-auto pb-2">
        <table ref="tableElementRef" class="w-max min-w-full text-left border-separate border-spacing-0" :style="{ minWidth: `${enforcedTableMinWidth}px` }">
          <thead>
            <!-- Double Layer Table Header Row -->
            <tr class="bg-white text-gray-700 text-xs tracking-wide font-bold sticky top-0 z-30">
              <th rowspan="2" class="px-4 py-4 border-r border-b border-red-100 align-bottom w-[230px] min-w-[230px] sticky left-0 z-40 bg-white">
                <button type="button" class="inline-flex items-center gap-1 hover:text-[#d10f2f] transition-colors" @click="toggleSort('name')">
                  <span>Désignation Matériel</span>
                  <span class="material-symbols-outlined text-sm">{{ getSortIcon('name') }}</span>
                </button>
              </th>
              <th rowspan="2" class="px-3 py-4 text-center border-r border-b border-red-100 bg-red-50 min-w-[110px] w-[110px]">
                <button type="button" class="inline-flex items-center gap-1 hover:text-[#d10f2f] transition-colors" @click="toggleSort('magasin')">
                  <span>Magasin</span>
                  <span class="material-symbols-outlined text-sm">{{ getSortIcon('magasin') }}</span>
                </button>
              </th>
              <th :colspan="displayedWarehouses.length" class="px-6 py-3 text-center border-r border-b border-red-100 bg-red-50 text-[#d10f2f] font-extrabold uppercase">Nos Entrepôts (Coselec)</th>
              <th :colspan="partnerWarehouseColumns.length" class="px-6 py-3 text-center border-b border-red-100 bg-red-100/40 text-[#97091f] font-extrabold uppercase">Stocks Déportés (Chez Partenaires)</th>
            </tr>
            <tr class="bg-white border-b border-red-100 text-gray-500 text-xs tracking-wide font-bold sticky top-[53px] z-20">
              <!-- Coselec Wh headers -->
              <th v-for="wh in displayedWarehouses" :key="wh.id" class="px-3 py-3 text-center border-r border-red-100 font-semibold min-w-[150px] max-w-[150px] truncate bg-white">
                <button type="button" class="inline-flex items-center gap-1 hover:text-[#d10f2f] transition-colors" @click="toggleSort(`wh:${wh.id}`)">
                  <span>{{ wh.name }}</span>
                  <span class="material-symbols-outlined text-sm">{{ getSortIcon(`wh:${wh.id}`) }}</span>
                </button>
              </th>
              <!-- Partner Wh headers -->
              <th v-for="column in partnerWarehouseColumns" :key="column.key" class="px-3 py-3 text-center border-r border-red-100 min-w-[170px] max-w-[170px] bg-white">
                <button type="button" class="inline-flex flex-col leading-tight hover:text-[#97091f] transition-colors" @click="toggleSort(`pt:${column.key}`)">
                  <span class="text-[11px] uppercase tracking-wide font-bold text-[#97091f] truncate">{{ column.partnerName }}</span>
                  <span class="text-[11px] text-gray-500 truncate">{{ column.warehouseName }}</span>
                  <span class="material-symbols-outlined text-sm text-gray-400">{{ getSortIcon(`pt:${column.key}`) }}</span>
                </button>
              </th>
            </tr>
          </thead>
          
          <tbody class="text-sm text-gray-700">
            <tr v-for="product in sortedInventory" :key="product.name" class="hover:bg-red-50/40 transition-colors">
              
              <!-- Product Identity Specs -->
              <td class="px-4 py-5 border-r border-b border-red-100 sticky left-0 z-10 bg-white">
                <div class="font-semibold text-gray-900">{{ product.name }}</div>
                <div class="text-xs text-gray-400 font-mono mt-0.5">SKU: {{ product.sku }}</div>
              </td>
              
              <!-- Central Unassigned Warehouse (Magasin) Quantity -->
              <td class="px-3 py-5 text-center border-r border-b border-red-100 bg-red-50">
                <span
                  :class="product.magasinQty > 0 ? 'bg-red-100 text-[#b3232b] border-red-200' : 'bg-white text-gray-300 border-gray-200'"
                  class="inline-flex min-w-[52px] justify-center px-2.5 py-1 rounded-full border text-sm font-semibold"
                >
                  {{ product.magasinQty || '-' }}
                </span>
              </td>
              
              <!-- Active Local Coselec Warehouse Cells -->
              <td v-for="whQty in product.localWhQuantities" :key="whQty.id" class="px-3 py-5 text-center border-r border-b border-red-100 text-gray-800">
                <span
                  :class="whQty.qty > 0 ? 'bg-red-50 text-[#d10f2f] border-red-200' : 'bg-white text-gray-300 border-gray-200'"
                  class="inline-flex min-w-[52px] justify-center px-2.5 py-1 rounded-full border text-sm font-semibold"
                >
                  {{ whQty.qty || '-' }}
                </span>
              </td>
              
              <!-- Partner External Warehouse Cells -->
              <td v-for="ptQty in product.partnerWhQuantities" :key="ptQty.key || ptQty.id" class="px-3 py-5 text-center border-r border-b border-red-100 text-gray-800">
                <span
                  :class="ptQty.qty > 0 ? 'bg-red-100/80 text-[#97091f] border-red-200' : 'bg-white text-gray-300 border-gray-200'"
                  class="inline-flex min-w-[52px] justify-center px-2.5 py-1 rounded-full border text-sm font-semibold"
                >
                  {{ ptQty.qty || '-' }}
                </span>
              </td>

            </tr>

            <!-- Empty Matrix Fallback -->
            <tr v-if="structuredInventory.length === 0">
              <td :colspan="2 + displayedWarehouses.length + partnerWarehouseColumns.length" class="px-6 py-12 text-center text-gray-400 border-b border-red-100">
                <p class="text-sm font-medium">Aucun article ne correspond à votre recherche</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  </AppLayout>
</template>

<style scoped>
.stock-table-scroll {
  -webkit-overflow-scrolling: touch;
  scrollbar-gutter: stable;
  overscroll-behavior-x: contain;
  touch-action: pan-x pan-y;
  scrollbar-width: auto;
}

.stock-table-scroll::-webkit-scrollbar {
  width: 10px;
  height: 12px;
}

.stock-table-scroll::-webkit-scrollbar-track {
  background: #fee2e2;
}

.stock-table-scroll::-webkit-scrollbar-thumb {
  background: #ef4444;
  border-radius: 9999px;
  border: 2px solid #fee2e2;
}

.mini-horizontal-scroll {
  accent-color: #d10f2f;
}

.mini-horizontal-scroll:disabled {
  opacity: 0.5;
}
</style>