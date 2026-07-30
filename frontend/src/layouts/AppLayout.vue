<script setup lang="ts">
import { ref } from 'vue';
import Navbar from '@/components/Navbar.vue';
import Sidebar from '@/components/Sidebar.vue';
import ChatModal from "@/components/chat/ChatModal.vue";

const isChatModalOpen = ref(false);

const toggleChat = () => {
    isChatModalOpen.value = !isChatModalOpen.value;
};
</script>

<template>
    <div class="flex h-screen overflow-hidden">
        <Sidebar />

        <div class="flex min-w-0 flex-1 flex-col">
            <Navbar />

            <main class="flex min-w-0 flex-1 overflow-y-auto bg-[#fff8f9] p-6">
                <slot />
            </main>
        </div>
    </div>

    <!-- Teleport to body guarantees it stays above ALL layout elements -->
    <Teleport to="body">
        <div class="z-9999">
            <button 
                type="button"
                class="flex h-16 fixed bottom-6 right-8 w-16 items-center justify-center rounded-full bg-red-500 text-white shadow-xl transition-all duration-200 hover:bg-red-600 hover:scale-110 active:scale-95 focus:outline-none"
                @click="toggleChat"
                aria-label="Toggle chat"
            >
                <span class="material-symbols-outlined text-2xl">chat</span>
            </button>

            <Transition
  				enter-active-class="transition duration-300 ease-out"
  				enter-from-class="transform opacity-0 scale-95 translate-y-4"
  				enter-to-class="transform opacity-100 scale-100 translate-y-0"
  				leave-active-class="transition duration-200 ease-in"
  				leave-from-class="transform opacity-100 scale-100 translate-y-0"
  				leave-to-class="transform opacity-0 scale-95 translate-y-4"
			>
				<ChatModal 
					v-if="isChatModalOpen" 
					@close="isChatModalOpen = false"
					class="fixed bottom-28 right-10 z-50 h-200 w-110 rounded-2xl border-2 border-red-400 bg-white shadow-2xl" 
				/>
			</Transition>
        </div>
    </Teleport>
</template>