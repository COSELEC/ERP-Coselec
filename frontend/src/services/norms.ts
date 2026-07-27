import api from "./api";

export interface NormCategory {
    id: int;
    name: string;
}

export interface NormVersion {
    id: number;
    norm_id: number;
    version_number: number;
    file_url: string;
    is_active: boolean;
    created_at: string;
}

export interface Norm {
    id: number;
    code: string;
    title: string;
    category_id: number;
    category?: NormCategory;
    versions: NormVersion[];
}

export const getCategories = async (): Promise<NormCategory[]> => {
    const response = await api.get("/norms/categories");
    return response.data;
};

export const getNorms = async (): Promise<Norm[]> => {
    const response = await api.get("/norms");
    return response.data;
};

export const createNorm = async (data: {code: string, title: string, category_id: number, file: File}): Promise<Norm> => {
    const formData = new FormData();
    formData.append("code", data.code);
    formData.append("title", data.title);
    formData.append("category_id", data.category_id.toString());
    formData.append("file", data.file);
    
    const response = await api.post("/norms", formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });
    return response.data;
};

export const deleteNorm = async (id: number): Promise<void> => {
    await api.delete(`/norms/${id}`);
};

export const uploadNormVersion = async (normId: number, data: {version_number: number, file: File}): Promise<NormVersion> => {
    const formData = new FormData();
    formData.append("version_number", data.version_number.toString());
    formData.append("file", data.file);
    const response = await api.post(`/norms/${normId}/versions`, formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });
    return response.data;
};

export const getNormHistory = async (normId: number): Promise<NormVersion[]> => {
    const response = await api.get(`/norms/${normId}/versions`);
    return response.data;
};
