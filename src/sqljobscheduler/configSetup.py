from pathlib import Path


def setup_config():
    get_config_dir().mkdir(parents=True, exist_ok=True)


def get_config_dir():
    return Path.home() / ".sqljobscheduler"


def get_queue_db_path():
    return get_config_dir() / "queueDB" / "analysis_jobs.db"


def get_log_dir():
    return get_config_dir() / "logs"


def get_repo_dir(file: str):
    return Path(file).parent.parent.parent


def get_server_service_dir(file: str):
    return get_repo_dir(file) / "ServerService"
