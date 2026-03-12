import { apiClient, apiUpload } from "@/lib/api";
import type { Asset } from "@/types";

export interface ImportResult {
  created: number;
  skipped_duplicate: number;
  errors: string[];
  total_parsed: number;
}

export const assetsApi = {
  getCompanyAssets: (companyId: string, skip = 0, limit = 200) =>
    apiClient.get<Asset[]>(
      `/assets?company_id=${encodeURIComponent(companyId)}&skip=${skip}&limit=${limit}`
    ),
  createAsset: (payload: {
    company_id: string;
    name: string;
    version?: string;
    type: "domain" | "ip_address" | "repository" | "library";
    source_file?: string;
  }) => apiClient.post<Asset>("/assets", payload),
  updateAsset: (assetId: string, payload: { name?: string; version?: string; type?: Asset["type"]; is_active?: boolean; source_file?: string }) =>
    apiClient.put<Asset>(`/assets/${assetId}`, payload),
  deleteAsset: (assetId: string) => apiClient.delete<{ message: string }>(`/assets/${assetId}`),
  importFromFile: (companyId: string, file: File) =>
    apiUpload<ImportResult>(`/assets/import?company_id=${encodeURIComponent(companyId)}`, file),
};
