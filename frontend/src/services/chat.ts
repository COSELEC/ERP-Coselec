import api from './api';

export interface Message {
  id: number;
  room_id: number;
  sender_id: number;
  sender_name: string;
  text: string | null;
  file_url: string | null;
  file_name: string | null;
  file_type: string | null;
  created_at: string;
}

export interface UploadResponse {
  file_url: string;
  file_name: string;
  file_type: string;
}

export interface ChatUser {
  id: number;
  name: string;
  email: string;
}

export interface ChatRoom {
  id: number;
  name: string;
  is_group: boolean;
  last_message: string | null;
  last_message_time: string | null;
  other_user_id: number | null;
}

export const ChatService = {
  async getUsers(): Promise<ChatUser[]> {
    const response = await api.get<ChatUser[]>('/chat/users');
    return response.data;
  },

  async getRooms(): Promise<ChatRoom[]> {
    const response = await api.get<ChatRoom[]>('/chat/rooms');
    return response.data;
  },

  async createOrGetRoom(userId: number): Promise<{ id: string }> {
    const response = await api.post<{ id: string }>('/chat/rooms', { user_id: userId });
    return response.data;
  },

  async createGroup(name: string, userIds: number[]): Promise<{ id: string }> {
    const response = await api.post<{ id: string }>('/chat/groups', { name, user_ids: userIds });
    return response.data;
  },
  /**
   * Fetch past message history for a specific room via HTTP GET
   */
  async getMessages(roomId: string, limit: number = 50): Promise<Message[]> {
    const response = await api.get<Message[]>(`/chat/${roomId}/messages`, {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Upload an image/file attachment via HTTP POST
   */
  async uploadFile(roomId: string, file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<UploadResponse>(`/chat/${roomId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Create a new WebSocket instance pointing to the backend chat endpoint
   */
  createWebSocket(roomId: string): WebSocket {
  // Le token est géré automatiquement par le navigateur via un cookie HttpOnly.
  // Plus besoin de le chercher dans le localStorage !
  const token = '';

  const isSecure = window.location.protocol === 'https:';
  const wsProtocol = isSecure ? 'wss:' : 'ws:';
  const host = `${window.location.hostname}:8000`;

  const wsUrl = `${wsProtocol}//${host}/chat/ws/${roomId}?token=${encodeURIComponent(token)}`;
  return new WebSocket(wsUrl);
},
  /**
   * Send text payload over an active WebSocket connection
   */
  sendTextMessage(socket: WebSocket, text: string) {
    this.sendMessage(socket, text, null);
  },

  /**
   * Send file payload over an active WebSocket connection
   */
  sendFileMessage(socket: WebSocket, fileData: UploadResponse) {
    this.sendMessage(socket, null, fileData);
  },

  /**
   * Send text and/or file payload over an active WebSocket connection
   */
  sendMessage(socket: WebSocket, text: string | null, fileData: UploadResponse | null = null) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          text,
          file_url: fileData ? fileData.file_url : null,
          file_name: fileData ? fileData.file_name : null,
          file_type: fileData ? fileData.file_type : null,
        })
      );
    }
  },

  /**
   * Resolve absolute URL for file download/viewing
   */
  getFileUrl(url: string | null): string | null {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    const baseUrl = api.defaults.baseURL || '';
    return `${baseUrl.replace(/\/+$/, '')}${url.startsWith('/') ? url : '/' + url}`;
  },
};