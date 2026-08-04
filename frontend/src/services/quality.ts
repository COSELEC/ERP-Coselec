import api from "./api";

export interface DocumentVersion {
  id: number;
  version_number: number;
  original_filename: string;
  r2_file_key: string;
  uploaded_by_id: number;
  uploaded_at: string;
}

export interface DocumentRoleReview {
  id: number;
  document_id: number;
  role_id: number;
  assigned_user_id: number | null;
  status: "PENDING" | "APPROVED" | "REJECTED";
  comment: string | null;
  reviewed_by_id: number | null;
  reviewed_at: string | null;
}

export interface QualityDocument {
  id: number;
  title: string;
  description: string | null;
  status: "IN_REVIEW" | "APPROVED" | "REJECTED" | "PUBLISHED";
  created_by_id: number;
  created_at: string;
  updated_at: string;
  versions: DocumentVersion[];
  role_reviews: DocumentRoleReview[];
  visible_roles?: { id: number; name: string }[];
}

export const qualityService = {
  async getAvailableRoles(): Promise<{ id: number; name: string; users: { id: number; name: string }[] }[]> {
    const response = await api.get("/quality/documents/available-roles");
    return response.data;
  },

  async getDocuments(filterPendingForMe = false): Promise<QualityDocument[]> {
    const response = await api.get("/quality/documents", {
      params: { filter_pending_for_me: filterPendingForMe },
    });
    return response.data;
  },

  async getLibraryDocuments(): Promise<QualityDocument[]> {
    const response = await api.get("/quality/documents/library");
    return response.data;
  },

  async updateDocumentVisibility(docId: number, roleIds: number[]): Promise<QualityDocument> {
    const response = await api.put(`/quality/documents/${docId}/visibility`, { role_ids: roleIds });
    return response.data;
  },

  async getDocument(docId: number): Promise<QualityDocument> {
    const response = await api.get(`/quality/documents/${docId}`);
    return response.data;
  },

  async createDocument(
    title: string,
    description: string,
    reviewers: { role_id: number; user_id: number | null }[],
    file: File
  ): Promise<QualityDocument> {
    const formData = new FormData();
    formData.append("title", title);
    if (description) formData.append("description", description);
    formData.append("reviewers_json", JSON.stringify(reviewers));
    formData.append("file", file);

    const response = await api.post("/quality/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  async uploadNewVersion(docId: number, file: File): Promise<QualityDocument> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(`/quality/documents/${docId}/versions`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  async submitReview(
    docId: number,
    reviewId: number,
    status: "APPROVED" | "REJECTED",
    comment?: string
  ): Promise<QualityDocument> {
    const response = await api.post(`/quality/documents/${docId}/reviews/${reviewId}`, {
      status,
      comment,
    });
    return response.data;
  },

  async getFileUrl(docId: number, versionId: number): Promise<string> {
    const response = await api.get(`/quality/documents/${docId}/download/${versionId}`);
    return response.data.url;
  },

  async deleteDocument(docId: number): Promise<void> {
    await api.delete(`/quality/documents/${docId}`);
  }
};
