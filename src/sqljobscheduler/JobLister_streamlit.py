import os
import base64
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd
import altair as alt
import streamlit as st
from sqljobscheduler import JobManager
from sqljobscheduler.LockFileUtils import check_gpu_lock_file, get_current_gpu_job


def create_gpu_usage_chart(jobs_df):
    """Create a timeline chart of GPU usage"""
    # Filter for jobs that have both start and end times
    usage_df = jobs_df[jobs_df["Started"] != "-"].copy()
    usage_df["Started"] = pd.to_datetime(usage_df["Started"])
    usage_df["Completed"] = pd.to_datetime(usage_df["Completed"].replace("-", pd.NaT))

    # For running jobs, use current time as end
    usage_df.loc[usage_df["Completed"].isna(), "Completed"] = pd.Timestamp.now()

    # Create timeline chart
    chart = (
        alt.Chart(usage_df)
        .mark_bar()
        .encode(
            x="Started",
            x2="Completed",
            y="User",
            color="Status",
            tooltip=["Program", "User", "Started", "Completed", "Status"],
        )
        .properties(height=200, title="GPU Usage Timeline")
    )

    return chart


def get_current_time():
    return datetime.now().strftime("%m/%d/%Y %H:%M")


def create_text_area(content: str, height: int = 300):
    st.text_area("Contents", value=content, height=height, label_visibility="collapsed")


def read_output_file(file_path: Path) -> str:
    try:
        result = subprocess.run(
            ["/usr/bin/cat", str(file_path)], capture_output=True, text=True
        )
        return result.stdout
    except FileNotFoundError:
        st.info("cat not found. Using fallback method")
        with open(file_path, "r") as file:
            return file.read()


def display_log_window():
    log_dir = Path(__file__).parent.parent.parent / "logs" / "job_runner"
    if not log_dir.exists():
        st.divider()
        st.subheader("No JR logs found")
        return None

    log_files = list(log_dir.glob("JR_*.log"))
    if not log_files:
        st.divider()
        st.subheader("No JR logs found")
        return None

    log_file = max(log_files, key=lambda x: x.stat().st_mtime)
    if log_file and log_file.exists():
        content = read_output_file(log_file)
        st.divider()
        st.subheader("Job Runner Status")
        create_text_area(content)
    else:
        st.divider()
        st.subheader("No logs for Job Runner found")


def display_curr_job_tmux_output():
    st.divider()
    st.subheader("Current Job")

    tmux4WA_dir = Path(__file__).parent.parent.parent / "logs" / "tmux4WA"
    tmux4WA_dir.mkdir(parents=True, exist_ok=True)
    current_job_log = tmux4WA_dir / "current_job"
    if check_gpu_lock_file():
        lock_info = get_current_gpu_job()
        if lock_info["ctype"] == "sql":
            try:
                st.write(f"Output for job {lock_info['job_id']:05d}:")
                result = subprocess.run(
                    [
                        "/usr/bin/tmux",
                        "-S",
                        f"/tmp/tmux-{os.getuid()}/gpuJobRunner",
                        "capture-pane",
                        "-t",
                        f"job_{lock_info['job_id']:05d}",
                        "-p",
                        "-S",
                        "-",
                    ],
                    capture_output=True,
                    text=True,
                )

                current_job_log.write_text(result.stdout)
                content = read_output_file(current_job_log)
                st.code(content, language="python", height=1000)
            except Exception as e:
                st.warning(f"Failed to capture tmux output: {e}")
        else:
            st.warning("CLI job currently running. Cannot display output")
    else:
        if current_job_log.exists():
            current_job_log.unlink()
        st.warning("No job currently running")


def shorten_path(path_str: str, parts: int = 3) -> str:
    """Shorten a path to show only the last N parts"""
    return str(Path(*Path(path_str).parts[-parts:]))


def get_basename(path_str: str) -> str:
    """Get the basename of a path"""
    return Path(path_str).name


def gpu_status_sidebar():
    st.sidebar.header("GPU Status")
    if check_gpu_lock_file():
        lock_info = get_current_gpu_job()
        if lock_info:
            st.sidebar.info("🔴 GPU Currently In Use")
            st.sidebar.write(f"**User:** {lock_info['user']}")
            st.sidebar.write(
                f"**Script:** {get_basename(lock_info['script']).replace('.py', '')}"
            )
            st.sidebar.write(f"**Started:** {lock_info['time started']}")
            st.sidebar.write(f"**PID:** {lock_info['pid']}")
            st.sidebar.write(f"**Type:** {lock_info['ctype']}")
            if lock_info.get("job_id"):
                st.sidebar.write(f"**Job ID:** {lock_info['job_id']:05d}")
    else:
        st.sidebar.success("🔵 GPU Available")


def set_title(LOGO_IMAGE: str, TITLE: str):
    """Set the title of the page

    Args:
        LOGO_IMAGE (str): Path to the logo image
        TITLE (str): Title of the page
    """
    st.markdown(
        """
    <style>
    .container {
        display: flex;
        gap: 10px;
        align-items: left;
    }
    .logo-text {
        font-weight:700 !important;
        font-size:50px !important;
    }
    .logo-img {
        float:right;
        height: 75px;
        width: 75px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
    <div class="container">
    <img class="logo-img" src="data:image/png ;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}">
        <p class="logo-text">{TITLE}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def main():
    root_dir = Path(__file__).parent.parent.parent
<<<<<<< HEAD
    img_dir = root_dir / "docs/images"
=======
    img_dir = root_dir / "docs/assets"
>>>>>>> 1cac9b6 (Initial commit: SQL Job Scheduler setup)
    png_path = img_dir / "gpuJobs.png"
    icon_path = img_dir / "gpuJobs.ico"

    st.set_page_config(
        page_title="GPU Jobs",
        page_icon=icon_path,
        layout="wide",
    )
    col1, col2 = st.columns([3, 1])
    with col1:
        set_title(png_path, "GPU Job Scheduler Dashboard")
    with col2:
        st.write(f"Last Updated: {get_current_time()}")
        if st.button("🔄 Refresh", key="refresh_button"):
            st.rerun()

    st.divider()

    # GPU Status
    gpu_status_sidebar()

    # Initialize queue
    db_path = "/mnt/EnvsDrive/scripts_dev/SQLJobScheduler/queueDB/analysis_jobs.db"
    queue = JobManager.JobQueue(db_path)

    st.subheader("Job Queue")

    # Get all jobs and convert to DataFrame
    jobs = queue.get_all_jobs()
    if not jobs:
        st.error("No jobs found in the database.")
        return

    today = datetime.now()

    filtered_jobs = [
        job
        for job in jobs
        if job.status == JobManager.JobStatus.PENDING
        or job.created_at.date() == today.date()
    ]

    if not filtered_jobs:
        st.info("No pending jobs found")
        display_log_window()
        display_curr_job_tmux_output()
        return

    df = pd.DataFrame(
        [
            {
                "ID": f"{job.id:05d}",
                "Program": get_basename(job.programPath).replace(".py", ""),
                "Python Exec": shorten_path(job.path2python_exec),
                "User": job.user,
                "Email": job.email_address,
                "Status": job.status.value,
                "Created": job.created_at.strftime("%Y-%m-%d %H:%M"),
                "Started": job.started_at.strftime("%Y-%m-%d %H:%M")
                if job.started_at
                else "-",
                "Completed": job.completed_at.strftime("%Y-%m-%d %H:%M")
                if job.completed_at
                else "-",
                "Error": (job.error_message[:50] + "...")
                if job.error_message and len(job.error_message) > 50
                else job.error_message or "-",
            }
            for job in jobs
            if (
                job.status == JobManager.JobStatus.PENDING
                or job.created_at.date() == today.date()
            )
        ]
    )

    # Filters
    status_filter = st.multiselect("Filter by Status", options=df["Status"].unique())

    # Apply filters
    if status_filter:
        df = df[df["Status"].isin(status_filter)]

    # Display table
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Display Job Runner Log
    display_log_window()
    # Display Current Job Output
    display_curr_job_tmux_output()


if __name__ == "__main__":
    main()
