import { apiClient } from "@/lib/api";
import type { Asset } from "@/types";

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
  deleteAsset: (assetId: string) => apiClient.delete<{ message: string }>(`/assets/${assetId}`),
};
