import {
  Box,
  Typography,
  Paper,
  IconButton,
  // useMediaQuery,
  Drawer,
  Button,
} from "@mui/material";
import { JobsTable } from "../components/JobsTable";
import { JobRunnerLog } from "../components/JobRunnerLog";
import { CurrentJob } from "../components/CurrentJob";
import { GPUStatus } from "../components/GPUStatus";
import {
  Job,
  GPUStatus as GPUStatusType,
  JobRunnerLog as JobRunnerLogType,
  CurrentJob as CurrentJobType,
} from "../types";
import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";
import MenuIcon from "@mui/icons-material/Menu";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import { useTheme } from "@mui/material/styles";
import { useState } from "react";
import { CircularProgress } from "@mui/material";
import { fetchDataPerConfig } from "../services/fetchData_utils";

/** Width of the sidebar drawer in pixels */
const DRAWER_WIDTH = 300;

/** Props for the Layout component */
interface LayoutProps {
  onToggleColorMode: () => void;
}

/**
 * Header component displaying the application title and theme toggle
 * @param {Object} props - Component props
 * @param {() => void} props.onToggleColorMode - Function to toggle between light/dark theme
 */
const Header = ({ onToggleColorMode }: { onToggleColorMode: () => void }) => {
  const theme = useTheme();
  return (
    <Paper
      sx={{
        p: 3,
        mb: 4,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <img
            src="/docs/images/gpuJobs.png"
            alt="GPU Job Scheduler Dashboard"
            style={{ width: "70px", height: "70px" }}
          />
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              GPU Jobs Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monitor GPU jobs in real-time
            </Typography>
          </Box>
        </Box>
      </Box>
      <IconButton onClick={onToggleColorMode} color="inherit">
        {theme.palette.mode === "dark" ? (
          <Brightness7Icon />
        ) : (
          <Brightness4Icon />
        )}
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
const Sidebar = ({
  open,
  onClose,
  gpuStatus,
}: {
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
      width: { xs: "100%", md: DRAWER_WIDTH },
      flexShrink: 0,
      "& .MuiDrawer-paper": {
        width: { xs: "100%", md: DRAWER_WIDTH },
        boxSizing: "border-box",
        p: { xs: 1, md: 2 },
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
  gpuStatusUpdatedAt,
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
  const isGPUAvailable = gpuStatus.status === "available";

  const formatLastUpdated = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: { xs: 1, md: 3 },
        width: "100%",
        transition: theme.transitions.create(["margin", "width"], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.enteringScreen,
        }),
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: { xs: 2, md: 3 },
        }}
      >
        <Button
          variant="outlined"
          startIcon={sidebarOpen ? <ChevronLeftIcon /> : <MenuIcon />}
          onClick={handleDrawerToggle}
          disabled={isGPUAvailable}
          sx={{
            color: isGPUAvailable ? "success.main" : "error.main",
            "&.Mui-disabled": {
              color: "success.main",
            },
            fontSize: { xs: "0.75rem", md: "0.875rem" },
            padding: { xs: "4px 8px", md: "6px 16px" },
          }}
        >
          GPU Status: {isGPUAvailable ? "Available" : "In Use"}
        </Button>
        <Box sx={{ display: "flex", gap: { xs: 1, md: 2 } }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              fontSize: { xs: "0.7rem", md: "0.75rem" },
            }}
          >
            Last update: {formatLastUpdated(gpuStatusUpdatedAt)}
          </Typography>
        </Box>
      </Box>
      <Box>
        <JobsTable jobs={jobs} />
      </Box>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            md: "1fr 1fr",
          },
          gap: { xs: 2, md: 3 },
        }}
      >
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
  // const theme = useTheme();
  // const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /**
   * Toggles the sidebar open/closed
   */
  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // get status for each API call
  const { gpuStatus, jobs, jobRunnerLog, currentJob } = fetchDataPerConfig([
    "gpuStatus",
    "jobs",
    "jobRunnerLog",
    "currentJob",
  ]);

  // Show loading spinner while data is being fetched
  if (
    gpuStatus.isLoading ||
    jobs.isLoading ||
    jobRunnerLog.isLoading ||
    currentJob.isLoading ||
    !gpuStatus.data
  ) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Header onToggleColorMode={onToggleColorMode} />
      <Box sx={{ display: "flex", flex: 1 }}>
        <Sidebar
          open={sidebarOpen}
          onClose={handleDrawerToggle}
          gpuStatus={gpuStatus.data}
        />
        <MainContent
          jobs={jobs.data}
          jobRunnerLog={jobRunnerLog.data}
          currentJob={currentJob.data}
          sidebarOpen={sidebarOpen}
          handleDrawerToggle={handleDrawerToggle}
          gpuStatus={gpuStatus.data}
          gpuStatusUpdatedAt={gpuStatus.dataUpdatedAt}
        />
      </Box>
    </Box>
  );
};
