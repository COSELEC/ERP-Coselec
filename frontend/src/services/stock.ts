  import api from './api';

  type MovementType = 'ENTRY' | 'EXIT';

  export const StockService = {
    getCategories() {
      return api.get('/categories/');
    },

    getProducts(categoryId?: number) {
      const url = categoryId ? `/products/?category_id=${categoryId}` : '/products/';
      return api.get(url);
    },

    getWarehouses() {
      return api.get('/warehouses/');
    },

    getPartners() {
      return api.get('/partners/');
    },

    getMovements() {
      return api.get('/stock-movements/');
    },

    createMovement(payload: {
      product_id: number;
      warehouse_id: number;
      quantity: number;
      type: MovementType;
      partner_id: number | null;
      notes?: string;
    }) {
      const movementUrl = payload.type === 'ENTRY' ? '/stock/entry/' : '/stock/exit/';

      return api.post(movementUrl, {
        product_id: payload.product_id,
        warehouse_id: payload.warehouse_id,
        quantity: payload.quantity,
        partner_id: payload.partner_id
      });
    },
    getStockOverview(){
      return api.get('/stocks/');
    },
    getGeneralStock() {
      return api.get('/stocks/general');
    },
    getProjectStock(projectId: number) {
      return api.get(`/stocks/projects/${projectId}`);
    },
    createCategory(payload: {name: string, description?: string; code?: string}){
      const normalizedCode = (payload.code || payload.name || 'CAT')
        .toUpperCase()
        .replace(/[^A-Z0-9]+/g, '_')
        .replace(/^_+|_+$/g, '')
        .slice(0, 24) || 'CAT';

      return api.post('/categories/', {
        code: normalizedCode,
        name: payload.name
      });
    },
    updateCategory(categoryId: number, payload: { name?: string; code?: string }) {
      const body: { name?: string; code?: string } = {};

      if (payload.name) {
        body.name = payload.name;
      }

      if (payload.code) {
        body.code = payload.code;
      }

      return api.put(`/categories/${categoryId}/`, body);
    },
    deleteCategory(categoryId: number) {
      return api.delete(`/categories/${categoryId}/`);
    },
    createProduct(payload: { name: string; sku_code: string; category_id: number; safety_threshold?: number }) {
      return api.post('/products/', {
        code: payload.sku_code,
        designation: payload.name,
        category_id: payload.category_id,
        minimum_stock: payload.safety_threshold ?? 0
      });
    },
    updateProduct(productId: number, payload: { name?: string; sku_code?: string; category_id?: number; safety_threshold?: number }) {
      const body: {
        designation?: string;
        code?: string;
        category_id?: number;
        minimum_stock?: number;
      } = {};

      if (payload.name) {
        body.designation = payload.name;
      }

      if (payload.sku_code) {
        body.code = payload.sku_code;
      }

      if (typeof payload.category_id === 'number') {
        body.category_id = payload.category_id;
      }

      if (typeof payload.safety_threshold === 'number') {
        body.minimum_stock = payload.safety_threshold;
      }

      return api.put(`/products/${productId}/`, body);
    },
    deleteProduct(productId: number) {
      return api.delete(`/products/${productId}/`);
    }
  };