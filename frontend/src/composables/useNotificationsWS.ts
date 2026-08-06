import { ref, computed } from 'vue';
import { getNotifications, markNotificationAsRead, type NotificationItem } from '@/services/notifications';
import { useToast } from '@/composables/useToast';

const notifications = ref<NotificationItem[]>([]);
const isConnected = ref(false);
let socket: WebSocket | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length);
const latestNotifications = computed(() => notifications.value.slice(0, 6));

async function loadInitialNotifications() {
  try {
    notifications.value = await getNotifications(false);
  } catch (err) {
    console.error('Error loading notifications:', err);
  }
}

async function markAsRead(notificationId: number) {
  try {
    await markNotificationAsRead(notificationId);
    notifications.value = notifications.value.filter(n => n.id !== notificationId);
  } catch (err) {
    console.error('Error marking notification as read:', err);
  }
}

function connectWS() {
  if (socket?.readyState === WebSocket.OPEN) return;

  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  if (!token) return;

  const isSecure = window.location.protocol === 'https:';
  const wsProtocol = isSecure ? 'wss:' : 'ws:';
  const host = window.location.host; // Use Vite's host and port
  const wsUrl = `${wsProtocol}//${host}/api/notifications/ws?token=${encodeURIComponent(token)}`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    isConnected.value = true;
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event_type === 'NEW_NOTIFICATION') {
        // Prepend new notification
        notifications.value.unshift(data.data);
        
        // Show toast
        const { info } = useToast();
        info(`Nouvelle notification: ${data.data.message}`);
      }
    } catch (err) {
      console.error('Error parsing WS message:', err);
    }
  };

  socket.onclose = () => {
    isConnected.value = false;
    socket = null;
    // Auto-reconnect after 3 seconds
    reconnectTimeout = setTimeout(() => {
      connectWS();
    }, 3000);
  };
}

function disconnectWS() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
  }
  if (socket) {
    socket.close();
    socket = null;
  }
  isConnected.value = false;
}

export function useNotificationsWS() {
  return {
    notifications,
    unreadCount,
    latestNotifications,
    isConnected,
    loadInitialNotifications,
    markAsRead,
    connectWS,
    disconnectWS
  };
}
