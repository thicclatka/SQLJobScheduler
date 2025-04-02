import { Card, CardContent, Typography, Chip, Box } from "@mui/material";
import { GPUStatus as GPUStatusType } from "../types";
import { formatDate } from "../utils/text_formatting";

interface GPUStatusProps {
  status: GPUStatusType;
}

export const GPUStatus = ({ status }: GPUStatusProps) => {
  const isInUse = status.status === "in_use";

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent sx={{ p: 2 }}>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          mb={2}
        >
          <Typography variant="h6" component="div" sx={{ fontSize: "1.1rem" }}>
            Current GPU Job Details
          </Typography>
        </Box>

        <Box display="flex" flexDirection="column" gap={1}>
          <Chip
            label={isInUse ? "In Use" : "Available"}
            color={isInUse ? "error" : "success"}
            size="small"
            sx={{ width: "fit-content" }}
          />
          {isInUse && status.user && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                User: {status.user}
              </Typography>
              {status.script && (
                <Typography variant="body2" color="text.secondary">
                  Script: {status.script}
                </Typography>
              )}
              {status.started && (
                <Typography variant="body2" color="text.secondary">
                  Started: {formatDate(status.started)}
                </Typography>
              )}
              {status.pid && (
                <Typography variant="body2" color="text.secondary">
                  PID: {status.pid}
                </Typography>
              )}
              {status.type && (
                <Typography variant="body2" color="text.secondary">
                  Type: {status.type}
                </Typography>
              )}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};
