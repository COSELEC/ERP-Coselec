<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { ChatService, type Message, type ChatRoom, type ChatUser } from '@/services/chat';

const emit = defineEmits(['close']);

const currentUserId = ref<number | null>(null);

const rooms = ref<ChatRoom[]>([]);
const availableUsers = ref<ChatUser[]>([]);
const activeRoomId = ref<string | null>(null);
const showUserList = ref(false);
const isGroupMode = ref(false);
const selectedUserIds = ref<number[]>([]);
const groupName = ref('');

const messages = ref<Message[]>([]);
const textInput = ref('');
const isLoading = ref(false);
const isCreatingRoom = ref(false);
const messageContainer = ref<HTMLElement | null>(null);
let socket: WebSocket | null = null;

const scrollToBottom = async () => {
  await nextTick();
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
};

watch(messages, () => scrollToBottom(), { deep: true });

const loadRooms = async () => {
  try {
    rooms.value = await ChatService.getRooms();
  } catch(e) { 
    console.error('Failed to load rooms', e);
  }
};

const loadUsers = async () => {
  try {
    availableUsers.value = await ChatService.getUsers();
  } catch(e) { 
    console.error('Failed to load users', e);
  }
};

const selectRoom = async (roomId: string) => {
  if (activeRoomId.value === roomId) return;
  activeRoomId.value = roomId;
  
  if (socket) {
    socket.close();
    socket = null;
  }
  
  isLoading.value = true;
  messages.value = [];
  try {
    messages.value = await ChatService.getMessages(roomId);
    initWebSocket(roomId);
    await scrollToBottom();
  } catch (err) {
    console.error('Failed to select room', err);
  } finally {
    isLoading.value = false;
  }
};

const startChatWith = async (userId: number) => {
  if (isGroupMode.value) {
    toggleUserSelection(userId);
    return;
  }
  isCreatingRoom.value = true;
  try {
    const res = await ChatService.createOrGetRoom(userId);
    await loadRooms();
    showUserList.value = false;
    selectRoom(res.id);
  } catch(e) {
    console.error('Failed to create room', e);
  } finally {
    isCreatingRoom.value = false;
  }
};

const toggleUserSelection = (userId: number) => {
  if (selectedUserIds.value.includes(userId)) {
    selectedUserIds.value = selectedUserIds.value.filter(id => id !== userId);
  } else {
    selectedUserIds.value.push(userId);
  }
};

const createGroup = async () => {
  if (!groupName.value.trim() || selectedUserIds.value.length === 0) return;
  isCreatingRoom.value = true;
  try {
    const res = await ChatService.createGroup(groupName.value.trim(), selectedUserIds.value);
    await loadRooms();
    showUserList.value = false;
    isGroupMode.value = false;
    selectedUserIds.value = [];
    groupName.value = '';
    selectRoom(res.id);
  } catch(e) {
    console.error('Failed to create group', e);
  } finally {
    isCreatingRoom.value = false;
  }
};

const initWebSocket = (roomId: string) => {
  socket = ChatService.createWebSocket(roomId);

  socket.onmessage = (event) => {
    const newMsg: Message = JSON.parse(event.data);
    messages.value.push(newMsg);
    // Reload rooms to update last message locally (simple approach)
    loadRooms();
  };

  socket.onerror = (err) => console.error('WebSocket Error:', err);
};

const selectedFile = ref<File | null>(null);

const handleSendMessage = async () => {
  const text = textInput.value.trim();
  const file = selectedFile.value;
  
  if ((!text && !file) || !socket || !activeRoomId.value) return;

  let uploadRes = null;
  if (file) {
    try {
      uploadRes = await ChatService.uploadFile(file);
    } catch (err) {
      console.error('File upload failed:', err);
      return;
    }
  }

  ChatService.sendMessage(socket, text || null, uploadRes);
  textInput.value = '';
  selectedFile.value = null;
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    selectedFile.value = target.files[0];
  }
  target.value = '';
};

const clearSelectedFile = () => {
  selectedFile.value = null;
};

onMounted(async () => {
  const userStr = localStorage.getItem('erp_current_user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      currentUserId.value = user.id;
    } catch (e) {}
  }
  
  await loadRooms();
  await loadUsers();
});

onUnmounted(() => {
  if (socket) socket.close();
});
</script>

<template>
  <div class="fixed bottom-24 right-8 w-[750px] bg-white rounded-2xl shadow-[0_10px_40px_rgba(179,12,39,0.2)] border border-red-100 flex flex-col overflow-hidden z-[9999]" style="height: 600px; max-height: 85vh;">
    <!-- Header -->
    <div class="px-4 py-3 bg-gradient-to-r from-[#b30c27] to-[#d10f2f] text-white flex justify-between items-center shadow-md z-20 relative">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined">chat</span>
        <h3 class="font-bold tracking-wide">Messagerie ERP</h3>
      </div>
      <button @click="$emit('close')" class="hover:bg-white/20 p-1.5 rounded-lg transition-colors flex items-center justify-center">
        <span class="material-symbols-outlined text-sm">close</span>
      </button>
    </div>

    <div class="flex flex-1 overflow-hidden relative">
      <!-- Sidebar: Discussions -->
      <div class="w-1/3 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div class="p-3 border-b border-gray-200 flex justify-between items-center bg-white z-10">
          <h4 class="font-semibold text-gray-700 text-sm">Discussions</h4>
          <button @click="showUserList = !showUserList" class="text-[#b30c27] hover:bg-red-50 p-1 rounded transition-colors" title="Nouvelle discussion">
            <span class="material-symbols-outlined text-lg">{{ showUserList ? 'close' : 'add_circle' }}</span>
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto">
          <!-- User selection dropdown/panel -->
          <div v-if="showUserList" class="bg-white border-b border-gray-100 p-3 shadow-inner flex flex-col gap-2">
            <!-- Mode Toggle -->
            <div class="flex items-center bg-gray-100 p-1 rounded-lg">
              <button @click="isGroupMode = false" :class="['flex-1 text-xs py-1.5 rounded-md transition-colors', !isGroupMode ? 'bg-white shadow-sm font-bold text-[#b30c27]' : 'text-gray-500 hover:text-gray-700']">Individuel</button>
              <button @click="isGroupMode = true" :class="['flex-1 text-xs py-1.5 rounded-md transition-colors', isGroupMode ? 'bg-white shadow-sm font-bold text-[#b30c27]' : 'text-gray-500 hover:text-gray-700']">Groupe</button>
            </div>

            <!-- Group Name Input (if group mode) -->
            <div v-if="isGroupMode" class="flex flex-col gap-1 mt-1">
              <input v-model="groupName" type="text" placeholder="Nom du groupe..." class="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:border-[#b30c27] focus:ring-1 focus:ring-[#b30c27] outline-none" />
            </div>

            <div class="text-xs text-gray-500 font-bold uppercase px-1 mt-1">Contacts disponibles</div>
            <div class="overflow-y-auto max-h-40 flex flex-col gap-1">
              <div v-if="availableUsers.length === 0" class="text-xs text-gray-400 p-1 text-center">Aucun utilisateur</div>
              <button v-for="u in availableUsers" :key="u.id" @click="startChatWith(u.id)"
                      :class="['w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center justify-between', isGroupMode && selectedUserIds.includes(u.id) ? 'bg-red-50 border border-red-200' : 'hover:bg-gray-50 border border-transparent']"
                      :disabled="isCreatingRoom">
                <div class="flex items-center gap-2 overflow-hidden">
                  <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-[#b30c27] font-bold shrink-0">
                    {{ u.name.charAt(0).toUpperCase() }}
                  </div>
                  <div class="overflow-hidden">
                    <p class="text-sm font-medium text-gray-800 truncate">{{ u.name }}</p>
                    <p class="text-[10px] text-gray-400 truncate">{{ u.email }}</p>
                  </div>
                </div>
                <span v-if="isGroupMode && selectedUserIds.includes(u.id)" class="material-symbols-outlined text-[#b30c27] text-sm">check_circle</span>
              </button>
            </div>

            <!-- Create Group Button -->
            <button v-if="isGroupMode" @click="createGroup" :disabled="!groupName.trim() || selectedUserIds.length === 0 || isCreatingRoom" class="mt-2 w-full bg-[#b30c27] text-white text-sm font-bold py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#d10f2f] transition-colors">
              Créer le groupe ({{ selectedUserIds.length }})
            </button>
          </div>

          <!-- Room List -->
          <div v-if="rooms.length === 0 && !showUserList" class="p-4 text-center text-sm text-gray-400 mt-4">
            Aucune discussion. Cliquez sur + pour commencer.
          </div>
          <button v-for="r in rooms" :key="r.id" @click="selectRoom(r.id.toString())"
                  :class="['w-full text-left px-3 py-3 border-b border-gray-100 transition-colors flex items-start gap-3', 
                           activeRoomId === r.id.toString() ? 'bg-red-50 border-l-4 border-l-[#b30c27]' : 'hover:bg-white bg-white border-l-4 border-l-transparent']">
             <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#b30c27] to-[#d10f2f] flex items-center justify-center text-white font-bold shrink-0">
                {{ r.name ? r.name.charAt(0).toUpperCase() : '?' }}
              </div>
              <div class="overflow-hidden flex-1">
                <div class="flex justify-between items-baseline mb-0.5">
                  <p class="text-sm font-bold text-gray-800 truncate pr-2">{{ r.name }}</p>
                  <span class="text-[10px] text-gray-400 shrink-0" v-if="r.last_message_time">
                    {{ new Date(r.last_message_time).toLocaleDateString() }}
                  </span>
                </div>
                <p class="text-xs text-gray-500 truncate">{{ r.last_message || 'Nouvelle discussion' }}</p>
              </div>
          </button>
        </div>
      </div>

      <!-- Main Chat Area -->
      <div class="w-2/3 flex flex-col bg-white">
        <template v-if="activeRoomId">
          <!-- Messages Container -->
          <div ref="messageContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-if="isLoading" class="flex justify-center py-4">
              <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#b30c27]"></div>
            </div>
            
            <div v-for="msg in messages" :key="msg.id" 
                 :class="['flex w-full', msg.sender_id === currentUserId ? 'justify-end' : 'justify-start']">
              <div :class="['max-w-[85%] rounded-2xl px-4 py-2 shadow-sm relative', 
                   msg.sender_id === currentUserId 
                     ? 'bg-gradient-to-br from-[#b30c27] to-[#d10f2f] text-white rounded-br-sm' 
                     : 'bg-gray-100 border border-gray-200 text-gray-800 rounded-bl-sm']">
                <p v-if="msg.sender_id !== currentUserId" class="text-xs font-bold text-[#b30c27] mb-1">
                  {{ msg.sender_name }}
                </p>
                <p class="text-sm break-words whitespace-pre-wrap">{{ msg.text }}</p>
                <div v-if="msg.file_url" class="mt-2">
                  <a :href="ChatService.getFileUrl(msg.file_url) || '#'" target="_blank" 
                     :class="['flex items-center gap-1 text-xs px-2 py-1.5 rounded-lg border transition-colors', 
                              msg.sender_id === currentUserId 
                                ? 'border-white/30 hover:bg-white/10 text-white' 
                                : 'border-gray-300 hover:bg-gray-200 text-gray-700']">
                    <span class="material-symbols-outlined text-sm">attach_file</span>
                    <span class="truncate max-w-[200px]">{{ msg.file_name }}</span>
                  </a>
                </div>
                <p :class="['text-[10px] text-right mt-1.5', msg.sender_id === currentUserId ? 'text-white/70' : 'text-gray-500']">
                  {{ msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Input Area -->
          <div class="p-3 bg-white border-t border-gray-100 flex flex-col gap-2 shadow-inner z-10">
            <!-- Selected File Preview -->
            <div v-if="selectedFile" class="flex items-center justify-between bg-red-50 px-3 py-2 rounded-lg border border-red-100">
              <div class="flex items-center gap-2 truncate">
                <span class="material-symbols-outlined text-[#b30c27] text-sm">attach_file</span>
                <span class="text-sm text-gray-700 truncate max-w-[300px]">{{ selectedFile.name }}</span>
              </div>
              <button @click="clearSelectedFile" class="text-gray-400 hover:text-red-500 rounded-full p-1 transition-colors flex items-center">
                <span class="material-symbols-outlined text-sm">close</span>
              </button>
            </div>
            
            <div class="flex items-end gap-2">
              <label class="cursor-pointer text-gray-400 hover:text-[#b30c27] transition-colors p-2 rounded-xl hover:bg-red-50 flex items-center justify-center mb-0.5">
                <span class="material-symbols-outlined">attach_file</span>
                <input type="file" class="hidden" @change="handleFileUpload" />
              </label>
              <textarea 
                v-model="textInput" 
                @keydown.enter.prevent="handleSendMessage"
                rows="1"
                placeholder="Votre message..."
                class="flex-1 bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#b30c27] focus:ring-1 focus:ring-[#b30c27] rounded-xl px-4 py-2.5 text-sm resize-none transition-shadow"
              ></textarea>
              <button 
                @click="handleSendMessage"
                :disabled="!textInput.trim() && !selectedFile"
                class="bg-[#d10f2f] text-white p-2.5 rounded-xl hover:bg-[#97091f] shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mb-0.5"
              >
                <span class="material-symbols-outlined text-sm">send</span>
              </button>
            </div>
          </div>
        </template>
        
        <template v-else>
          <div class="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-50">
             <span class="material-symbols-outlined text-6xl opacity-20 mb-4">forum</span>
             <p>Sélectionnez une discussion pour commencer</p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>