import api from './api';

export const employeeService = {
  getAllEmployees: async () => {
    try {
      const response = await api.get('/employees/');
      return response; 
    } catch (error) {
      console.error('Error fetching employees:', error);
      throw error;
    }
  },
  getEmployee: async (id: number) => {
    try {
      const response = await api.get(`/employees/${id}`);
      return response;
    } catch (error) {
      console.error('Error fetching employee:', error);
      throw error;
    }
  },
  createEmployee: async (data: any) => {
    try {
      const response = await api.post('/employees/', data);
      return response;
    } catch (error) {
      console.error('Error creating employee:', error);
      throw error;
    }
  },
  updateEmployee: async (id: number, data: any) => {
    try {
      const response = await api.put(`/employees/${id}`, data);
      return response;
    } catch (error) {
      console.error('Error updating employee:', error);
      throw error;
    }
  },
  deleteEmployee: async (id: number) => {
    try {
      const response = await api.delete(`/employees/${id}`);
      return response;
    } catch (error) {
      console.error('Error deleting employee:', error);
      throw error;
    }
  },
  getOrgChart: async () => {
    try {
      const response = await api.get('/employees/org-chart');
      return response;
    } catch (error) {
      console.error('Error fetching org chart:', error);
      throw error;
    }
  }

};