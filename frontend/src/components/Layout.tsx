import { Box, Typography, Paper, IconButton, useMediaQuery, Drawer, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { JobsTable } from './JobsTable';
import { JobRunnerLog } from './JobRunnerLog';
import { CurrentJob } from './CurrentJob';
import { GPUStatus } from './GPUStatus';
import { Job, GPUStatus as GPUStatusType, JobRunnerLog as JobRunnerLogType, CurrentJob as CurrentJobType } from '../types';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import { useTheme } from '@mui/material/styles';
import { useState } from 'react';
import { CircularProgress } from '@mui/material';

/**
 * Constants for data refetch intervals
 * FAST: 5 seconds for critical real-time data (GPU status, current job)
 * NORMAL: 30 seconds for less critical data (jobs list, logs)
 */
const REFETCH_INTERVAL = {
  FAST: 5000,    
  NORMAL: 30000  
};

/** Width of the sidebar drawer in pixels */
const DRAWER_WIDTH = 300;

/**
 * Custom hook for fetching and caching data from the API
 * @template T - The type of data being fetched
 * @param {string} key - The API endpoint key
 * @param {T} defaultValue - Default value to use if data is not available
 * @param {number} interval - Refetch interval in milliseconds
 * @returns {Object} Query result containing data, loading state, and error state
 */
const useData = <T,>(key: string, defaultValue: T, interval: number = REFETCH_INTERVAL.NORMAL) => {
  return useQuery<T>({
    queryKey: [key],
    queryFn: () => fetch(`/api/${key}`).then(res => res.json()),
    refetchInterval: interval,
    select: (data) => data || defaultValue,
    refetchIntervalInBackground: true,
  });
};

/** Props for the Layout component */
interface LayoutProps {
  onToggleColorMode: () => void;
}

/**
 * Header component displaying the application title and theme toggle
 * @param {Object} props - Component props
 * @param {() => void} props.onToggleColorMode - Function to toggle between light/dark theme
 */
const Header = ({ onToggleColorMode }: { 
  onToggleColorMode: () => void; 
}) => {
  const theme = useTheme();
  return (
    <Paper sx={{ p: 3, mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <img 
            src="/docs/images/gpuJobs.png" 
            alt="GPU Job Scheduler Dashboard" 
            style={{ width: '60px', height: '60px' }} 
          />
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              GPU Jobs
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monitor GPU jobs in real-time
            </Typography>
          </Box>
        </Box>
      </Box>
      <IconButton onClick={onToggleColorMode} color="inherit">
        {theme.palette.mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
      </IconButton>
    </Paper>
  );
};

/**
 * Sidebar component displaying GPU status information
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the sidebar is open
 * @param {() => void} props.onClose - Function to close the sidebar
 * @param {GPUStatusType} props.gpuStatus - Current GPU status information
 */
const Sidebar = ({ open, onClose, gpuStatus }: { 
  open: boolean; 
  onClose: () => void; 
  gpuStatus: GPUStatusType; 
}) => (
  <Drawer
    variant="temporary"
    anchor="left"
    open={open}
    onClose={onClose}
    sx={{
      width: DRAWER_WIDTH,
      flexShrink: 0,
      '& .MuiDrawer-paper': {
        width: DRAWER_WIDTH,
        boxSizing: 'border-box',
      },
    }}
  >
    <GPUStatus status={gpuStatus} />
  </Drawer>
);

/**
 * Main content area displaying jobs table, logs, and current job information
 * @param {Object} props - Component props
 * @param {Job[]} props.jobs - List of jobs to display
 * @param {JobRunnerLogType} [props.jobRunnerLog] - Job runner log information
 * @param {CurrentJobType} [props.currentJob] - Currently running job information
 * @param {boolean} props.sidebarOpen - Whether the sidebar is open
 * @param {() => void} props.handleDrawerToggle - Function to toggle the sidebar
 * @param {GPUStatusType} props.gpuStatus - Current GPU status information
 */
const MainContent = ({ 
  jobs, 
  jobRunnerLog, 
  currentJob, 
  sidebarOpen, 
  handleDrawerToggle, 
  gpuStatus,
  gpuStatusUpdatedAt
}: { 
  jobs: Job[]; 
  jobRunnerLog?: JobRunnerLogType; 
  currentJob?: CurrentJobType;
  sidebarOpen: boolean;
  handleDrawerToggle: () => void;
  gpuStatus: GPUStatusType;
  gpuStatusUpdatedAt: number;
}) => {
  const theme = useTheme();
  const isGPUAvailable = gpuStatus.status === 'available';
  
  const formatLastUpdated = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };
  
  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        width: '100%',
        transition: theme.transitions.create(['margin', 'width'], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.enteringScreen,
        }),
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={sidebarOpen ? <ChevronLeftIcon /> : <MenuIcon />}
          onClick={handleDrawerToggle}
          disabled={isGPUAvailable}
          sx={{ 
            color: isGPUAvailable ? 'success.main' : 'error.main',
            '&.Mui-disabled': {
              color: 'success.main'
            }
          }}
        >
          GPU Status: {isGPUAvailable ? 'Available' : 'In Use'}
        </Button>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Last update: {formatLastUpdated(gpuStatusUpdatedAt)}
          </Typography>
        </Box>
      </Box>
      <Box>
        <JobsTable jobs={jobs} />
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: { md: '1fr 1fr' }, gap: 3 }}>
        {jobRunnerLog && <JobRunnerLog log={jobRunnerLog} />}
        {currentJob && <CurrentJob job={currentJob} />}
      </Box>
    </Box>
  );
};

/**
 * Main Layout component that orchestrates the entire application layout
 * Manages the sidebar state and data fetching for all components
 * @param {Object} props - Component props
 * @param {() => void} props.onToggleColorMode - Function to toggle between light/dark theme
 */
export const Layout = ({ onToggleColorMode }: LayoutProps) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /**
   * Toggles the sidebar open/closed
   */
  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Fetch data with appropriate refetch intervals
  const { data: gpuStatus, isLoading: isLoadingGPU, dataUpdatedAt: gpuStatusUpdatedAt } = useData<GPUStatusType>('gpu-status', { 
    status: 'available'
  }, REFETCH_INTERVAL.FAST);
  const { data: jobs = [], isLoading: isLoadingJobs, dataUpdatedAt: jobsUpdatedAt } = useData<Job[]>('jobs', []);
  const { data: jobRunnerLog, isLoading: isLoadingLog } = useData<JobRunnerLogType>('job-runner-log', { content: '' });
  const { data: currentJob, isLoading: isLoadingCurrentJob, dataUpdatedAt: currentJobUpdatedAt } = useData<CurrentJobType>('current-job', { type: 'none' }, REFETCH_INTERVAL.FAST);

  // Show loading spinner while data is being fetched
  if (isLoadingGPU || isLoadingJobs || isLoadingLog || isLoadingCurrentJob || !gpuStatus) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header onToggleColorMode={onToggleColorMode} />
      <Box sx={{ display: 'flex', flex: 1 }}>
        <Sidebar open={sidebarOpen} onClose={handleDrawerToggle} gpuStatus={gpuStatus} />
        <MainContent 
          jobs={jobs} 
          jobRunnerLog={jobRunnerLog} 
          currentJob={currentJob}
          sidebarOpen={sidebarOpen}
          handleDrawerToggle={handleDrawerToggle}
          gpuStatus={gpuStatus}
          gpuStatusUpdatedAt={gpuStatusUpdatedAt}
        />
      </Box>
    </Box>
  );
};