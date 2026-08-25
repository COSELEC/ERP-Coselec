import api from './api';

export interface Permission {
  id: number;
  code: string;
  name: string;
  description: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions: Permission[];
}

export interface RoleCreate {
  name: string;
  description?: string;
  permission_codes: string[];
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permission_codes?: string[];
}

export const roleService = {
  async getPermissions(): Promise<Permission[]> {
    const response = await api.get<Permission[]>('/permissions');
    return response.data;
  },

  async getRoles(): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles');
    return response.data;
  },

  async getRole(id: number): Promise<Role> {
    const response = await api.get<Role>(`/roles/${id}`);
    return response.data;
  },

  async createRole(data: RoleCreate): Promise<Role> {
    const response = await api.post<Role>('/roles', data);
    return response.data;
  },

  async updateRole(id: number, data: RoleUpdate): Promise<Role> {
    const response = await api.put<Role>(`/roles/${id}`, data);
    return response.data;
  },

  async deleteRole(id: number): Promise<void> {
    await api.delete(`/roles/${id}`);
  }
};
