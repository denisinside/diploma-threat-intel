import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assetsApi } from "./api";

export function useAssets(companyId?: string) {
  return useQuery({
    queryKey: ["assets", companyId],
    queryFn: () => assetsApi.getCompanyAssets(companyId as string),
    enabled: Boolean(companyId),
  });
}

export function useCreateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: assetsApi.createAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: assetsApi.deleteAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useImportAssets() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ companyId, file }: { companyId: string; file: File }) =>
      assetsApi.importFromFile(companyId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}
