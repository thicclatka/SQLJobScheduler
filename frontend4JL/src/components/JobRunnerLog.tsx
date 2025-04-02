import {
  Typography,
  Box,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
} from "@mui/material";
import { JobRunnerLog as JobRunnerLogType } from "../types";
import { useState } from "react";
import { useRemoveOldLogs } from "../services/fetchData_utils";
import DeleteIcon from "@mui/icons-material/Delete";

const DAYS_TO_KEEP_LOG = 7;

interface JobRunnerLogProps {
  log: JobRunnerLogType;
}

export const JobRunnerLog = ({ log }: JobRunnerLogProps) => {
  const [currentIndex, setCurrentIndex] = useState(
    Number(localStorage.getItem("selectedLogIndex") || 0)
  );
  const [openDialog, setOpenDialog] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error";
  }>({
    open: false,
    message: "",
    severity: "success",
  });
  const removeOldLogsMutation = useRemoveOldLogs();

  const handleRemoveOldLogs = async () => {
    try {
      const result = await removeOldLogsMutation.mutateAsync();
      setOpenDialog(false);
      setSnackbar({
        open: true,
        message: result.message,
        severity: "success",
      });
    } catch (error) {
      console.error("Failed to remove old logs:", error);
      setSnackbar({
        open: true,
        message: "Failed to remove old logs",
        severity: "error",
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6">Job Runner Log</Typography>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Select Date</InputLabel>
            <Select
              value={currentIndex}
              label="Select Date"
              onChange={(e) => {
                const newIndex = Number(e.target.value);
                setCurrentIndex(newIndex);
                localStorage.setItem("selectedLogIndex", newIndex.toString());
              }}
            >
              {log.availableDates.map((date, index) => (
                <MenuItem key={date} value={index}>
                  {date}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>
      <Box
        sx={{
          bgcolor: "background.default",
          p: 2,
          borderRadius: 1,
          maxHeight: "400px",
          overflow: "auto",
        }}
      >
        <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
          {log.content[currentIndex]}
        </pre>
      </Box>
      <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 2 }}>
        {log.availableDates.length > DAYS_TO_KEEP_LOG && (
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setOpenDialog(true)}
            disabled={removeOldLogsMutation.isPending}
          >
            Remove Old Logs
          </Button>
        )}
      </Box>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Remove Old Logs</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove logs older than 7 days? This action
            cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleRemoveOldLogs}
            color="error"
            disabled={removeOldLogsMutation.isPending}
          >
            {removeOldLogsMutation.isPending ? "Removing..." : "Remove"}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
};
