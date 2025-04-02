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
} from "@mui/material";
import { Job } from "../types";
import { formatDate, getStatusColor } from "../utils/text_formatting";

interface JobsTableProps {
  jobs: Job[];
}

export const JobsTable = ({ jobs }: JobsTableProps) => {
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

        {jobs.length === 0 ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight={200}
          >
            <Typography color="text.secondary">
              No pending jobs in queue
            </Typography>
          </Box>
        ) : (
          <TableContainer
            component={Paper}
            sx={{ bgcolor: "background.paper" }}
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Program</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Completed</TableCell>
                  <TableCell>Error</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>{job.id}</TableCell>
                    <TableCell>{job.program}</TableCell>
                    <TableCell>{job.user}</TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{formatDate(job.created)}</TableCell>
                    <TableCell>{formatDate(job.started)}</TableCell>
                    <TableCell>{formatDate(job.completed)}</TableCell>
                    <TableCell>{job.error}</TableCell>
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
