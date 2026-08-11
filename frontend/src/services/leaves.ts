import api from "./api";

export interface LeaveRequest {
  id: number;
  employee_id: number;
  leave_type: string;
  start_date: string;
  end_date: string;
  status: string;
  reason: string | null;
  pdf_url: string | null;
  justificatif_url: string | null;
}

export interface LeaveRequestCreate {
  employee_id: number;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string | null;
}

export const leaveService = {
  async getByEmployee(employeeId: number): Promise<LeaveRequest[]> {
    const response = await api.get<any[]>("/requests/?type=LEAVE");
    const mapped = response.data.map((req: any) => ({
      id: req.id,
      employee_id: req.payload.employee_id || req.requester_id,
      leave_type: req.payload.leave_type || "Congé",
      start_date: req.payload.start_date,
      end_date: req.payload.end_date,
      status: req.status,
      reason: req.payload.reason || null,
      pdf_url: req.attachment_url || null,
      justificatif_url: null
    }));
    return mapped.filter((leave: LeaveRequest) => leave.employee_id === employeeId);
  },

  async create(leaveData: LeaveRequestCreate): Promise<LeaveRequest> {
    const payload = {
      type: "LEAVE",
      priority: "NORMAL",
      category: "RH",
      payload: {
        type: "LEAVE",
        employee_id: leaveData.employee_id,
        leave_type: leaveData.leave_type,
        start_date: leaveData.start_date,
        end_date: leaveData.end_date,
        reason: leaveData.reason
      }
    };
    const response = await api.post<any>("/requests/", payload);
    const req = response.data;
    return {
      id: req.id,
      employee_id: req.payload.employee_id || req.requester_id,
      leave_type: req.payload.leave_type || "Congé",
      start_date: req.payload.start_date,
      end_date: req.payload.end_date,
      status: req.status,
      reason: req.payload.reason || null,
      pdf_url: req.attachment_url || null,
      justificatif_url: null
    };
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/requests/${id}`);
  },

  async downloadCertificate(id: number): Promise<void> {
    const response = await api.get<Blob>(
      `/requests/${id}/download-pdf`,
      { responseType: 'blob' }
    );

    let fileName = `conge_${id}.pdf`;
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        fileName = match[1];
      }
    }

    const url = window.URL.createObjectURL(response.data);
    const link = window.document.createElement('a');
    link.href = url;
    link.download = fileName;
    window.document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};