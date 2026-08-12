import { api } from './api';

export interface WeeklyReportCreate {
  project_id: number;
  report_date: string;       
  week_start?: string;       
  week_end?: string;         
  hours_worked: number;
  progress_percentage?: number;
  tasks_completed: string;
  issues_encountered?: string;
  plan_next_week?: string;
}

export interface WeeklyReportResponse {
  id: number;
  user_id: number;
  project_id: number;
  week_start: string;
  week_end: string;
  report_date: string;
  hours_worked: number;
  progress_percentage?: number;
  tasks_completed: string;
  issues_encountered?: string;
  plan_next_week?: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED';
  created_at: string;
  updated_at: string;
}

export type DailyReportCreate = WeeklyReportCreate;
export type DailyReportResponse = WeeklyReportResponse;

export const dailyReportsService = {
  async submitReport(data: WeeklyReportCreate, photos: File[] = []): Promise<WeeklyReportResponse> {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value.toString());
      }
    });
    photos.forEach(photo => formData.append('photos', photo));
    
    const response = await api.post<WeeklyReportResponse>('/reports/weekly', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async submitDailyReport(data: DailyReportCreate, photos: File[] = []): Promise<DailyReportResponse> {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value.toString());
      }
    });
    photos.forEach(photo => formData.append('photos', photo));
    
    const response = await api.post<DailyReportResponse>('/reports/daily', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async getReports(projectId?: number, weekStart?: string): Promise<WeeklyReportResponse[]> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId.toString());
    if (weekStart) params.append('week_start', weekStart);
    const response = await api.get<WeeklyReportResponse[]>(`/reports/weekly?${params.toString()}`);
    return response.data;
  },

  async updateStatus(reportId: number, status: 'DRAFT' | 'SUBMITTED' | 'APPROVED'): Promise<WeeklyReportResponse> {
    const response = await api.patch<WeeklyReportResponse>(`/reports/weekly/${reportId}/status?status=${status}`);
    return response.data;
  },

  async getDailyReports(projectId?: number, reportDate?: string): Promise<DailyReportResponse[]> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId.toString());
    if (reportDate) params.append('report_date', reportDate);
    const response = await api.get<DailyReportResponse[]>(`/reports/daily?${params.toString()}`);
    return response.data;
  },

  async updateDailyStatus(reportId: number, status: 'DRAFT' | 'SUBMITTED' | 'APPROVED'): Promise<DailyReportResponse> {
    const response = await api.patch<DailyReportResponse>(`/reports/daily/${reportId}/status?status=${status}`);
    return response.data;
  },
};
