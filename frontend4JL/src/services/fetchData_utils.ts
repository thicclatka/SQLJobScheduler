import { useQuery, UseQuery, UseQueryResult } from "@tanstack/react-query";
import { GPUStatus, Job, JobRunnerLog, CurrentJob } from "../types";

// constants for data refetch intervals
/**
 * Constants for data refetch intervals
 * FAST: 5 seconds for critical real-time data (GPU status, current job)
 * NORMAL: 30 seconds for less critical data (jobs list, logs)
 */
export const REFETCH_INTERVAL = {
  FAST: 5000,
  NORMAL: 30000,
};

// setting up config for each API call
/**
 * Type-safe configuration for data fetching
 * Each entry defines the key, default value, and refetch interval
 */
const createConfigEntry = (
  key: string,
  defaultValue: any,
  interval: number = REFETCH_INTERVAL.NORMAL,
): DataFetchConfigEntry => ({
  key,
  defaultValue,
  interval,
});

export const dataFetchConfig = {
  gpuStatus: createConfigEntry(
    "gpu-status",
    { status: "available" } as GPUStatus,
    REFETCH_INTERVAL.NORMAL,
  ),
  jobs: createConfigEntry("jobs", [] as Job[], REFETCH_INTERVAL.NORMAL),
  jobRunnerLog: createConfigEntry(
    "job-runner-log",
    { content: [], availableDates: [], log_files: [] } as JobRunnerLog,
    REFETCH_INTERVAL.NORMAL,
  ),
  currentJob: createConfigEntry(
    "current-job",
    { type: "none" } as CurrentJob,
    REFETCH_INTERVAL.FAST,
  ),
} as const;

// Type for the config object
export type DataFetchConfig = typeof dataFetchConfig;

// Type for a single config entry
export type DataFetchConfigEntry = {
  key: string;
  defaultValue: any;
  interval?: number;
};

// Type for the results of all data fetches
export type DataFetchResults = {
  [K in keyof DataFetchConfig]: {
    data: DataFetchConfig[K]["defaultValue"];
    isLoading: boolean;
    dataUpdatedAt: number;
  };
};

// Setting up functions for each API call

/**
 * Custom hook for fetching and caching data from the API
 * @template T - The type of data being fetched
 * @param key - The API endpoint key
 * @param defaultValue - Default value to use if data is not available
 * @param interval - Refetch interval in milliseconds (defaults to NORMAL)
 * @returns Query result containing data, loading state, and error state
 */
export const fetchData = <T>(
  key: string,
  defaultValue: T,
  interval: number = REFETCH_INTERVAL.NORMAL,
  queryParams: string = "",
): UseQueryResult<T> => {
  return useQuery<T>({
    queryKey: [key, queryParams],
    queryFn: () => fetch(`/api/${key}`).then((res) => res.json()),
    refetchInterval: interval,
    select: (data: T) => data || defaultValue,
    refetchIntervalInBackground: true,
  });
};

/**
 * Custom hook that fetches all configured data endpoints
 * @returns Object containing all fetched data with their loading states
 */
export const fetchDataPerConfig = <K extends keyof DataFetchConfig>(
  configKeys: K[],
  overrideDefault?: Partial<DataFetchConfig>,
): DataFetchResults => {
  return configKeys.reduce((acc, configKey) => {
    const config = dataFetchConfig[configKey];
    const defaultValue = overrideDefault?.[configKey] || config.defaultValue;
    const { data, isLoading, dataUpdatedAt } = fetchData(
      config.key,
      defaultValue,
      config.interval,
    );

    return {
      ...acc,
      [configKey]: {
        data: data || config.defaultValue,
        isLoading,
        dataUpdatedAt,
      },
    };
  }, {} as DataFetchResults);
};
