import os

VALID_QUEUES = {"high_priority", "small_files", "large_files"}
DEFAULT_QUEUE = os.getenv("DEFAULT_QUEUE", "small_files")
