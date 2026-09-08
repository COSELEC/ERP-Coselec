<template>
  <div 
    class="relative inline-flex items-center justify-center rounded-full shrink-0 select-none overflow-hidden transition-transform duration-200"
    :class="[sizeClasses, customClass]"
    :title="displayName"
  >
    <img 
      v-if="effectivePhotoUrl && !imageFailed"
      :src="effectivePhotoUrl"
      :alt="displayName"
      class="h-full w-full object-cover"
      @error="imageFailed = true"
    />
    <div 
      v-else
      class="h-full w-full flex items-center justify-center font-bold tracking-wider text-white shadow-inner"
      :class="gradientClass"
    >
      {{ initials }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { resolveStorageUrl } from '@/utils/fileUrl';

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

interface UserLike {
  name?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  photo_url?: string | null;
  email?: string | null;
}

const props = withDefaults(
  defineProps<{
    user?: UserLike | null;
    photoUrl?: string | null;
    name?: string | null;
    size?: AvatarSize;
    customClass?: string;
  }>(),
  {
    user: null,
    photoUrl: null,
    name: null,
    size: 'md',
    customClass: '',
  }
);

const imageFailed = ref(false);

const rawPhotoUrl = computed(() => {
  return props.photoUrl || props.user?.photo_url || null;
});

const effectivePhotoUrl = computed(() => {
  return resolveStorageUrl(rawPhotoUrl.value);
});

// Reset failed flag if photo URL changes
watch(effectivePhotoUrl, () => {
  imageFailed.value = false;
});

const displayName = computed(() => {
  if (props.name) return props.name;
  if (props.user?.name) return props.user.name;
  if (props.user?.first_name || props.user?.last_name) {
    return `${props.user.first_name || ''} ${props.user.last_name || ''}`.trim();
  }
  if (props.user?.email) return props.user.email;
  return 'Utilisateur';
});

const initials = computed(() => {
  const name = displayName.value.trim();
  if (!name) return 'U';
  const parts = name.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0]![0]! + parts[1]![0]!).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
});

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'xs':
      return 'w-6 h-6 text-[10px] ring-1 ring-white/30';
    case 'sm':
      return 'w-8 h-8 text-xs ring-1 ring-red-100';
    case 'md':
      return 'w-10 h-10 text-sm ring-2 ring-white shadow-sm';
    case 'lg':
      return 'w-14 h-14 text-base ring-2 ring-red-100 shadow-sm';
    case 'xl':
      return 'w-20 h-20 text-xl ring-4 ring-white shadow-md';
    case '2xl':
      return 'w-28 h-28 text-3xl ring-4 ring-white shadow-lg';
    default:
      return 'w-10 h-10 text-sm ring-2 ring-white shadow-sm';
  }
});

// Deterministic gradient based on user name/initials
const gradients = [
  'bg-gradient-to-tr from-red-600 to-rose-500',
  'bg-gradient-to-tr from-rose-600 to-red-400',
  'bg-gradient-to-tr from-amber-600 to-red-500',
  'bg-gradient-to-tr from-[#97091f] to-[#d10f2f]',
  'bg-gradient-to-tr from-slate-700 to-red-800',
  'bg-gradient-to-tr from-red-700 to-orange-600',
];

const gradientClass = computed(() => {
  const str = displayName.value;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % gradients.length;
  return gradients[index];
});
</script>
