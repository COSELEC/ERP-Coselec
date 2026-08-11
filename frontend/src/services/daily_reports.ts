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
  async submitReport(data: WeeklyReportCreate): Promise<WeeklyReportResponse> {
    const response = await api.post<WeeklyReportResponse>('/weekly-reports', data);
    return response.data;
  },

  async getReports(projectId?: number, weekStart?: string): Promise<WeeklyReportResponse[]> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId.toString());
    if (weekStart) params.append('week_start', weekStart);
    const response = await api.get<WeeklyReportResponse[]>(`/weekly-reports?${params.toString()}`);
    return response.data;
  },

  async updateStatus(reportId: number, status: 'DRAFT' | 'SUBMITTED' | 'APPROVED'): Promise<WeeklyReportResponse> {
    const response = await api.patch<WeeklyReportResponse>(`/weekly-reports/${reportId}/status`, { status });
    return response.data;
  },
};
