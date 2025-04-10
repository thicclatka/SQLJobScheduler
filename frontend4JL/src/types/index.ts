export interface GPUStatus {
  status: "in_use" | "available";
  user?: string;
  script?: string;
  started?: string;
  pid?: string;
  type?: string;
  job_id?: number;
}

export interface Job {
  id: string;
  program: string;
  python_exec: string;
  user: string;
  email: string;
  status: string;
  created: string;
  started: string;
  completed: string;
  parameters: string;
  error: string;
}

export interface JobRunnerLog {
  log_files: string[];
  content: string[];
  availableDates: string[];
}

export interface CurrentJob {
  content?: string;
  error?: string;
  type: "sql" | "cli" | "none";
  job_id?: number;
}

export interface RemoveJobLogsResult {
  message: string;
  removed_count: number;
}
