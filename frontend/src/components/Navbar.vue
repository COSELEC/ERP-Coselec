<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";
import {
    getNotifications,
    markNotificationAsRead,
    type NotificationItem,
} from "@/services/notifications";
import {
    clearStoredProfile,
    getStoredProfile,
    refreshCurrentUserProfile,
    type CurrentUserProfile,
} from "@/services/session";
import { logout as logoutRequest } from "@/services/auth";

const router = useRouter();
const notifications = ref<NotificationItem[]>([]);
const isOpen = ref(false);
const isLoading = ref(false);
const profile = ref<CurrentUserProfile | null>(getStoredProfile());
let pollingTimer: ReturnType<typeof setInterval> | null = null;

const unreadCount = computed(() => {
    return notifications.value.filter((item) => !item.is_read).length;
});

const latestNotifications = computed(() => {
    return notifications.value.slice(0, 6);
});

const currentUserName = computed(() => {
    return profile.value?.name || "Utilisateur";
});

const currentUserRole = computed(() => {
    const firstRole = profile.value?.roles?.[0];
    return firstRole || "Utilisateur";
});

const currentUserInitial = computed(() => {
    const name = currentUserName.value.trim();
    return name ? name.charAt(0).toUpperCase() : "U";
});

async function loadNotifications() {
    isLoading.value = true;
    try {
        notifications.value = await getNotifications(false);
    } catch (error) {
        console.error("Unable to load notifications", error);
    } finally {
        isLoading.value = false;
    }
}

function togglePanel() {
    isOpen.value = !isOpen.value;

    if (isOpen.value) {
        loadNotifications();
    }
}

async function markAsRead(notificationId: number) {
    try {
        await markNotificationAsRead(notificationId);
        notifications.value = notifications.value.filter(
            (item) => item.id !== notificationId
        );
    } catch (error) {
        console.error("Unable to mark notification as read", error);
    }
}

function handleDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement | null;
    if (!target) {
        return;
    }

    if (!target.closest("[data-notification-panel]")) {
        isOpen.value = false;
    }
}

function handleNotificationsRefresh() {
    loadNotifications();
}

onMounted(() => {
    loadNotifications();
    document.addEventListener("click", handleDocumentClick);
    window.addEventListener("notifications:refresh", handleNotificationsRefresh);

    refreshCurrentUserProfile()
        .then((value) => {
            profile.value = value;
        })
        .catch(() => {
            profile.value = getStoredProfile();
        });
        
    pollingTimer = setInterval(() => {
        loadNotifications();
    }, 30000);
});

onBeforeUnmount(() => {
    document.removeEventListener("click", handleDocumentClick);
    window.removeEventListener("notifications:refresh", handleNotificationsRefresh);
    if (pollingTimer) {
        clearInterval(pollingTimer);
    }
});

async function logout() {
    try {
        await logoutRequest();
    } catch {
        // Keep local cleanup even if backend logout fails.
    } finally {
        localStorage.removeItem("access_token");
        sessionStorage.removeItem("access_token");
        clearStoredProfile();
        router.push("/login");
    }
}
</script>

<template>
    <header
        class="relative h-16 bg-white border-b border-red-100 px-6 flex items-center justify-between"
    >
        <div>
            <h1 class="text-xl font-bold text-[#d10f2f]">
                ERP COSELEC
            </h1>
        </div>

        <div class="flex items-center gap-6">
            <RouterLink
                to="/home"
                class="text-gray-600 hover:text-[#d10f2f] transition font-semibold"
                >
                <button class="flex items-center gap-2 p-2 rounded-lg hover:bg-red-50 transition">
                    <span class="material-symbols-outlined text-[#d10f2f]">
                        home
                    </span>
                    Accueil
                </button>  
            </RouterLink>
            <div class="text-gray-600 hover:text-[#d10f2f] transition font-semibold">
            <button
                data-notification-panel
                @click.stop="togglePanel"
                class="relative p-2 rounded-lg hover:bg-red-50 transition flex items-center gap-2 p-2 rounded-lg hover:bg-red-50 transition"
            >
                <span class="material-symbols-outlined text-[#d10f2f]">
                    notifications

                </span>

                <span
                    v-if="unreadCount > 0"
                    class="absolute -right-1 -top-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white"
                >
                    {{ unreadCount }}
                </span>
                Notifications   
            </button>
            </div>

            <div
                v-if="isOpen"
                data-notification-panel
                class="absolute right-28 top-14 z-40 w-[360px] overflow-hidden rounded-2xl border border-red-100 bg-white shadow-[0_18px_40px_rgba(127,7,28,0.18)]"
            >
                <div class="border-b border-red-100 bg-gradient-to-r from-red-50 to-white px-4 py-3">
                    <p class="text-sm font-bold text-gray-900">Notifications</p>
                    <p class="text-xs text-gray-500">{{ unreadCount }} non lue(s)</p>
                </div>

                <div class="max-h-80 overflow-y-auto p-2">
                    <p v-if="isLoading" class="px-3 py-4 text-sm text-gray-500">Chargement...</p>

                    <div
                        v-for="item in latestNotifications"
                        :key="item.id"
                        class="mb-2 rounded-xl border px-3 py-3"
                        :class="item.is_read ? 'border-gray-100 bg-white' : 'border-red-100 bg-red-50/50'"
                    >
                        <p class="text-sm font-medium text-gray-800">{{ item.message }}</p>
                        <div class="mt-2 flex items-center justify-between">
                            <span class="text-xs text-gray-400">{{ item.created_at }}</span>
                            <button
                                v-if="!item.is_read"
                                class="text-xs font-semibold text-red-600 hover:text-red-700"
                                @click="markAsRead(item.id)"
                            >
                                Marquer lu
                            </button>
                        </div>
                    </div>

                    <p
                        v-if="!isLoading && latestNotifications.length === 0"
                        class="px-3 py-4 text-sm text-gray-500"
                    >
                        Aucune notification.
                    </p>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <div
                    class="h-10 w-10 rounded-full bg-[#d10f2f] text-white flex items-center justify-center"
                >
                    {{ currentUserInitial }}
                </div>

                <div>
                    <p class="font-semibold">
                        {{ currentUserName }}
                    </p>

                    <p class="text-xs text-gray-500">
                        {{ currentUserRole }}
                    </p>
                </div>
            </div>

            
<button class="flex items-center gap-2 text-[#d10f2f] hover:bg-red-50 transition p-2 rounded-lg" @click="logout">
  <span class="material-symbols-outlined">
    logout
  </span>
</button>

        </div>
    </header>
</template>