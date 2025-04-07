import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
} from "@mui/material";
import { Job } from "../types";
import { formatDate, getStatusColor } from "../utils/text_formatting";
import { useState, useMemo } from "react";

interface JobsTableProps {
  jobs: Job[];
}

export const JobsTable = ({ jobs }: JobsTableProps) => {
  const [statusFilter, setStatusFilter] = useState("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  // Get unique status values for the status filter
  const uniqueStatuses = useMemo(() => {
    return Array.from(new Set(jobs.map((job) => job.status)));
  }, [jobs]);

  // Filter the jobs based on the filter values
  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const matchesStatus = !statusFilter || job.status === statusFilter;

      // Convert job dates to Date objects for comparison
      const jobDate = new Date(job.created);
      const start = startDate ? new Date(startDate) : null;
      const end = endDate ? new Date(endDate) : null;

      // Check if job date is within the selected range
      const matchesDateRange =
        (!start || jobDate >= start) && (!end || jobDate <= end);

      return matchesStatus && matchesDateRange;
    });
  }, [jobs, statusFilter, startDate, endDate]);

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          mb={2}
        >
          <Typography variant="h6" component="div">
            Jobs Queue
          </Typography>
        </Box>

        {/* Filter Bar */}
        <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All Statuses</MenuItem>
              {uniqueStatuses.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            size="small"
            type="date"
            label="Start Date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            type="date"
            label="End Date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </Box>

        {filteredJobs.length === 0 ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight={200}
          >
            <Typography color="text.secondary">
              No jobs found matching filters
            </Typography>
          </Box>
        ) : (
          <TableContainer
            component={Paper}
            sx={{
              bgcolor: "background.paper",
              maxHeight: 440, // Fixed height for scrolling
              overflow: "auto",
            }}
          >
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell width="5%">ID</TableCell>
                  <TableCell width="10%">Program</TableCell>
                  <TableCell width="10%">Email</TableCell>
                  <TableCell width="10%">Status</TableCell>
                  <TableCell width="10%">Created</TableCell>
                  <TableCell width="10%">Started</TableCell>
                  <TableCell width="10%">Completed</TableCell>
                  <TableCell width="30%">Error</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredJobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell width="5%">{job.id}</TableCell>
                    <TableCell width="10%">{job.program}</TableCell>
                    <TableCell width="10%">{job.email}</TableCell>
                    <TableCell width="10%">
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell width="10%">{formatDate(job.created)}</TableCell>
                    <TableCell width="10%">{formatDate(job.started)}</TableCell>
                    <TableCell width="10%">
                      {formatDate(job.completed)}
                    </TableCell>
                    <TableCell
                      width="30%"
                      sx={{
                        maxWidth: 0,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {job.error}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  );
};
