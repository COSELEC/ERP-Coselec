import { ref, watch, onUnmounted, type Ref } from 'vue';

export function useDebounceFn<T extends (...args: any[]) => any>(fn: T, delay = 300) {
  let timer: ReturnType<typeof setTimeout> | null = null;

  const debounced = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn(...args);
    }, delay);
  };

  const cancel = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  };

  onUnmounted(() => {
    cancel();
  });

  return {
    debounced,
    cancel,
  };
}

export function useDebouncedRef<T>(initialValue: T, delay = 300) {
  const state = ref(initialValue) as Ref<T>;
  const debouncedState = ref(initialValue) as Ref<T>;
  let timer: ReturnType<typeof setTimeout> | null = null;

  watch(state, (newVal) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      debouncedState.value = newVal;
    }, delay);
  });

  onUnmounted(() => {
    if (timer) clearTimeout(timer);
  });

  return {
    value: state,
    debouncedValue: debouncedState,
  };
}
