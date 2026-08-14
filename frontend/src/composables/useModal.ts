import { ref } from 'vue';

export function useModal<T = any>(initialState = false) {
  const isOpen = ref(initialState);
  const selectedItem = ref<T | null>(null);

  const open = (item?: T) => {
    if (item !== undefined) {
      selectedItem.value = item;
    }
    isOpen.value = true;
  };

  const close = () => {
    isOpen.value = false;
    selectedItem.value = null;
  };

  const toggle = () => {
    isOpen.value = !isOpen.value;
    if (!isOpen.value) {
      selectedItem.value = null;
    }
  };

  return {
    isOpen,
    selectedItem,
    open,
    close,
    toggle,
  };
}
