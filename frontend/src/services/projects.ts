import api from './api';

export const projectService = {
  getAllProjects: () => api.get('/projects/'),
  getProjectById: (projectId: number) => api.get(`/projects/${projectId}`),
  createProject: (data: any) => api.post('/projects/', data),
  updateProject: (projectId: number, data: any) => api.patch(`/projects/${projectId}`, data),
  getProjectMilestones: (projectId: number) => api.get(`/projects/${projectId}/milestones`),
};

export const taskService = {
  getTasksByProject: (projectId: number, milestoneId?: number) => {
    let url = `/projects/${projectId}/tasks`;
    if (milestoneId) url += `?milestone_id=${milestoneId}`;
    return api.get(url);
  },
  createTask: (projectId: number, data: any) => api.post(`/projects/${projectId}/tasks/`, data),
  
  updateTask: (projectId:number,taskId: number, data: any) => api.patch(`/projects/${projectId}/tasks/${taskId}`, data),
  deleteTask: (projectId: number, taskId: number) => api.delete(`/projects/${projectId}/tasks/${taskId}`),

  uploadTaskDocuments: (projectId: number, taskId: number, files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return api.post(`/projects/${projectId}/tasks/${taskId}/documents`, formData);
  },

  getTaskDocuments: (projectId: number, taskId: number) =>
    api.get(`/projects/${projectId}/tasks/${taskId}/documents`),

  deleteTaskDocument: (projectId: number, documentId: number) =>
    api.delete(`/projects/${projectId}/tasks/documents/${documentId}`),

  downloadTaskDocument: async (projectId: number, documentId: number, fallbackFileName: string) => {
    const response = await api.get(`/projects/${projectId}/tasks/documents/${documentId}/download`, {
      responseType: 'blob',
    });

    const blobUrl = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = fallbackFileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  }
};

export const updateProjectTask = async (projectId: number, taskId: number, taskData: any) => {
  const response = await api.patch(`/projects/${projectId}/tasks/${taskId}`, taskData);
  return response.data;
}