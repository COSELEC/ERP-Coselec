import api from "./api";

export interface KPIValue {
  id: number;
  indicator_id: number;
  year: number;
  month: number;
  value_raw: string | null;
  value_numeric: number | null;
}

export interface KPIYearlyTarget {
  id: number;
  indicator_id: number;
  year: number;
  frequency: string | null;
  target_raw: string | null;
  target_numeric: number | null;
  target_numeric_max: number | null;
  operator: "GTE" | "LTE" | "BETWEEN" | "EQ" | null;
}

export interface KPIIndicator {
  id: number;
  processus_id: number;
  name: string;
  yearly_targets: KPIYearlyTarget[];
  values: KPIValue[];
}

export interface KPIProcessus {
  id: number;
  name: string;
  department_id: number | null;
  indicators: KPIIndicator[];
}

export const kpiService = {
  async uploadPreview(file: File): Promise<string[]> {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await api.post("/kpi/upload-preview", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data.sheet_names;
  },

  async uploadParse(
    file: File, 
    sheetName: string, 
    year: number, 
    monthName: string, 
    monthIndex: number
  ): Promise<{ message: string, imported_count: number, updated_count: number }> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sheet_name", sheetName);
    formData.append("year", year.toString());
    formData.append("month_name", monthName);
    formData.append("month_index", monthIndex.toString());

    const response = await api.post("/kpi/upload-parse", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  async getDashboardData(year: number): Promise<KPIProcessus[]> {
    const response = await api.get(`/kpi/dashboard/${year}`);
    return response.data;
  },

  async createProcessus(name: string, department_id?: number | null): Promise<KPIProcessus> {
    const response = await api.post("/kpi/processus", { name, department_id });
    return response.data;
  },

  async createIndicator(name: string, processus_id: number): Promise<KPIIndicator> {
    const response = await api.post("/kpi/indicators", { name, processus_id });
    return response.data;
  },

  async updateKpiValue(indicator_id: number, year: number, month: number, value_raw: string, value_numeric: number | null): Promise<KPIValue> {
    const response = await api.post("/kpi/values", { indicator_id, year, month, value_raw, value_numeric });
    return response.data;
  }
};
