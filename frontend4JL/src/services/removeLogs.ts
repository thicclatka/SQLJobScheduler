import { useMutation } from "@tanstack/react-query";
import { useQueryClient } from "@tanstack/react-query";

// function for removing old logs
export const removeOldLogs = async () => {
  const response = await fetch("/api/remove_job_logs", {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to remove old logs");
  }
  return response.json();
};

export const useRemoveOldLogs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeOldLogs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobRunnerLog"] });
    },
  });
};
