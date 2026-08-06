import api from "./api";

export interface EmployeeDocument {
  id: number;
  employee_id: number;
  category: string;
  file_name: string;
  storage_path: string;
  mime_type: string | null;
  numero: string | null;
  expiry_date: string | null;
  is_verified: boolean;
}

export const documentService = {
  // Récupérer les documents d'un employé spécifique
  async getByEmployee(employeeId: number): Promise<EmployeeDocument[]> {
    const response = await api.get<EmployeeDocument[]>(`/users/${employeeId}/documents`);
    return response.data;
  },

  // Uploader un nouveau document (utilisation de FormData)
  async upload(employeeId: number, file: File, category: string, numero?: string, expiryDate?: string): Promise<EmployeeDocument> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    
    if (numero) {
      formData.append('numero', numero);
    }
    
    if (expiryDate) {
      formData.append('expiry_date', expiryDate);
    }

    const response = await api.post<EmployeeDocument>(
      `/users/${employeeId}/documents`, 
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  async download(documentId: number, fileName: string): Promise<void> {
    const response = await api.get<Blob>(
      `/users/documents/${documentId}/download`,
      {
        responseType: 'blob'
      }
    );

    const url = window.URL.createObjectURL(response.data);
    const link = window.document.createElement('a');
    link.href = url;
    link.download = fileName;
    window.document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Supprimer un document
  async delete(documentId: number): Promise<void> {
    await api.delete(`/users/documents/${documentId}`);
  }
};