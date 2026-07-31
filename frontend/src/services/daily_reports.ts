import { api } from './api';

export interface DailyReportCreate {
  project_id: number;
  report_date: string;
  hours_worked: number;
  progress_percentage?: number;
  tasks_completed: string;
  issues_encountered?: string;
  plan_for_tomorrow?: string;
}

export interface DailyReportResponse extends DailyReportCreate {
  id: number;
  employee_id: number;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED';
  created_at: string;
  updated_at: string;
}

export const dailyReportsService = {
  async submitReport(data: DailyReportCreate): Promise<DailyReportResponse> {
    const response = await api.post<DailyReportResponse>('/daily-reports', data);
    return response.data;
  },

  async getReports(projectId?: number, date?: string): Promise<DailyReportResponse[]> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId.toString());
    if (date) params.append('report_date', date);
    
    const response = await api.get<DailyReportResponse[]>(`/daily-reports?${params.toString()}`);
    return response.data;
  },

  async updateStatus(reportId: number, status: 'DRAFT' | 'SUBMITTED' | 'APPROVED'): Promise<DailyReportResponse> {
    const response = await api.patch<DailyReportResponse>(`/daily-reports/${reportId}/status`, { status });
    return response.data;
  }
};
