import api from "./api";

export interface Contract {
  id: number;
  user_id: number;
  contract_type: string;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
}

export interface ContractCreate {
  user_id: number;
  contract_type: string;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
}

export const contractService = {
  async getAll(): Promise<Contract[]> {
    const response = await api.get<Contract[]>("/contracts");
    return response.data;
  },

  async create(contract: ContractCreate): Promise<Contract> {
    const response = await api.post<Contract>("/contracts", contract);
    return response.data;
  },

  async update(id: number, contract: Partial<ContractCreate>): Promise<Contract> {
    const response = await api.put<Contract>(`/contracts/${id}`, contract);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/contracts/${id}`);
  }
};