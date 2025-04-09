import { Card, CardContent, Typography, Box, Paper } from "@mui/material";
import { CurrentJob as CurrentJobType } from "../types";

interface CurrentJobProps {
  job: CurrentJobType;
}

export const CurrentJob = ({ job }: CurrentJobProps) => {
  const getContent = () => {
    if (job.type === "none") {
      return "No job currently running";
    } else if (job.type === "cli") {
      return "CLI job currently running. Cannot display output";
    } else if (job.type === "sql") {
      if (job.error) {
        return job.error;
      }
      return job.content || "No output available";
    }
    return "Unknown job type";
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          mb={2}
        >
          <Typography variant="h6" component="div">
            Current Job Output
          </Typography>
        </Box>

        <Paper
          sx={{
            p: 2,
            maxHeight: "400px",
            overflow: "auto",
            bgcolor: "background.paper",
            fontFamily: "monospace",
            fontSize: "0.8rem",
            whiteSpace: "pre-wrap",
          }}
        >
          {getContent()}
        </Paper>
      </CardContent>
    </Card>
  );
};
