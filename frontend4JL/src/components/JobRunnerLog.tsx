import { Card, CardContent, Typography, Box, Paper } from '@mui/material';
import { JobRunnerLog as JobRunnerLogType } from '../types';

interface JobRunnerLogProps {
  log: JobRunnerLogType;
}

export const JobRunnerLog = ({ log }: JobRunnerLogProps) => {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" component="div">
            Job Runner Log
          </Typography>
        </Box>
        
        <Paper
          sx={{
            p: 2,
            maxHeight: 300,
            overflow: 'auto',
            bgcolor: 'background.paper',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            whiteSpace: 'pre-wrap',
          }}
        >
          {log.content}
        </Paper>
      </CardContent>
    </Card>
  );
}; 