import api from './api';

export interface Role {
  id: number;
  name: string;
}

export interface User {
  id: number;
  name: string;
  first_name?: string;
  last_name?: string;
  status?: string;
  email: string;
  roles: Role[];
}

export interface UserListResponse {
  total: number;
  page: number;
  size: number;
  items: User[];
}

export interface UserCreate {
  name?: string;
  first_name?: string;
  last_name?: string;
  status?: string;
  email: string;
  role_name: string;
}

export interface UserUpdate {
  name?: string;
  first_name?: string;
  last_name?: string;
  status?: string;
  email?: string;
  role_name?: string;
}

export interface CreateUserResponse {
  user: User;
  temporary_password?: string;
}

export const userService = {
  async getUsers(skip: number = 0, limit: number = 10, search?: string): Promise<UserListResponse> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (search) {
        params.append('search', search);
    }
    const response = await api.get<UserListResponse>('/users/', { params });
    return response.data;
  },

  async createUser(data: UserCreate): Promise<CreateUserResponse> {
    const response = await api.post<CreateUserResponse>('/users/', data);
    return response.data;
  },

  async updateUser(id: number, data: UserUpdate): Promise<User> {
    const response = await api.put<User>(`/users/${id}`, data);
    return response.data;
  },

  async deleteUser(id: number): Promise<void> {
    await api.delete(`/users/${id}`);
  }
};
