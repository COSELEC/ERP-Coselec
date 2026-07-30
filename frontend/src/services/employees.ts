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
  deleteEmployee: async (id: number) => {
    try {
      const response = await api.delete(`/employees/${id}`);
      return response;
    } catch (error) {
      console.error('Error deleting employee:', error);
      throw error;
    }
  }
};