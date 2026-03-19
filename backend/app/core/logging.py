import logging
import sys

from pythonjsonlogger.json import JsonFormatter


class _WarnLevelFormatter(JsonFormatter):
    """WARNING → WARN 매핑으로 Go(slog)와 레벨명 통일"""

    def process_log_record(self, log_record: dict) -> dict:
        level = log_record.get("level", "")
        if level == "WARNING":
            log_record["level"] = "WARN"
        return super().process_log_record(log_record)


def init_logger(level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)
    formatter = _WarnLevelFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "asctime": "time",
            "levelname": "level",
            "name": "source",
        },
        datefmt="%Y-%m-%dT%H:%M:%S.%f%z",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Uvicorn 로거 포맷 통일
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
