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
  Tooltip,
} from "@mui/material";
import { Job } from "../types";
import { formatDate, getStatusColor } from "../utils/text_formatting";
import { useState, useMemo } from "react";

interface JobsTableProps {
  jobs: Job[];
}

const FilterBarForJobsTable = ({
  statusFilter,
  setStatusFilter,
  uniqueStatuses,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
}: {
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  uniqueStatuses: string[];
  startDate: string;
  setStartDate: (date: string) => void;
  endDate: string;
  setEndDate: (date: string) => void;
}) => (
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

    <TextField_forDate
      label="Start Date"
      value={startDate}
      setValue={setStartDate}
    />
    <TextField_forDate label="End Date" value={endDate} setValue={setEndDate} />
  </Box>
);

const TextField_forDate = ({
  label,
  value,
  setValue,
}: {
  label: string;
  value: string;
  setValue: (value: string) => void;
}) => (
  <TextField
    size="small"
    type="date"
    label={label}
    value={value}
    onChange={(e) => setValue(e.target.value)}
    InputLabelProps={{ shrink: true }}
  />
);

const TableCell_withTooltip = ({
  job_text,
  width,
}: {
  job_text: string;
  width: string;
}) => {
  const parsed_job_text = (() => {
    try {
      // First try to parse as is
      const parsed = JSON.parse(job_text);
      return JSON.stringify(parsed, null, 1);
    } catch {
      return job_text;
    }
  })();

  return (
    <TableCell
      width={width}
      sx={{
        maxWidth: "200px",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
        position: "relative",
      }}
    >
      <Tooltip
        title={
          <Box
            component="pre"
            sx={{
              margin: 0,
              whiteSpace: "pre-wrap",
              fontFamily: "monospace",
              fontSize: "0.8rem",
            }}
          >
            {parsed_job_text}
          </Box>
        }
        placement="top"
        arrow
        enterDelay={500}
      >
        <Box
          component="span"
          sx={{
            cursor: "help",
            display: "block",
            width: "100%",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {job_text}
        </Box>
      </Tooltip>
    </TableCell>
  );
};

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
        <FilterBarForJobsTable
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          uniqueStatuses={uniqueStatuses}
          startDate={startDate}
          setStartDate={setStartDate}
          endDate={endDate}
          setEndDate={setEndDate}
        />
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
                  <TableCell width="15%">Parameters</TableCell>
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
                    <TableCell_withTooltip
                      job_text={job.parameters}
                      width="15%"
                    />
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
                    <TableCell_withTooltip job_text={job.error} width="30%" />
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
