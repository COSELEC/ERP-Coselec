import { ref, computed, type Ref } from 'vue';

export type SortOrder = 'asc' | 'desc';

export function useTableSort<T = any>(
  items?: Ref<T[]>,
  initialColumn = '',
  initialOrder: SortOrder = 'asc'
) {
  const sortColumn = ref<string>(initialColumn);
  const sortOrder = ref<SortOrder>(initialOrder);

  const sortBy = (column: string) => {
    if (sortColumn.value === column) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn.value = column;
      sortOrder.value = 'asc';
    }
  };

  const toggleSort = (column: string) => {
    if (sortColumn.value === column) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn.value = column;
      sortOrder.value = 'desc';
    }
  };

  const sortItems = (list: T[], column = sortColumn.value, order = sortOrder.value): T[] => {
    if (!column || !list || list.length === 0) return list ? [...list] : [];
    return [...list].sort((a: any, b: any) => {
      let valA = a?.[column];
      let valB = b?.[column];

      if (valA === null || valA === undefined) valA = '';
      if (valB === null || valB === undefined) valB = '';

      if (typeof valA === 'string' && typeof valB === 'string') {
        const compareRes = valA.localeCompare(valB, 'fr', { numeric: true, sensitivity: 'base' });
        return order === 'asc' ? compareRes : -compareRes;
      }

      if (valA < valB) return order === 'asc' ? -1 : 1;
      if (valA > valB) return order === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const sortedItems = computed(() => {
    if (!items || !items.value) return [];
    return sortItems(items.value);
  });

  return {
    sortColumn,
    sortOrder,
    sortBy,
    toggleSort,
    sortItems,
    sortedItems,
  };
}
