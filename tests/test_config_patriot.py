import json
import os
import threading
from pathlib import Path
import pytest
import logging

from config_patriot_env import atomic_write_json, verify_config_manifest

def make_logger():
    logger = logging.getLogger("pytest_logger")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)
    return logger

def test_atomic_write_json_success(tmp_path):
    logger = make_logger()
    dir_path = tmp_path / "cfgdir"
    dir_path.mkdir()
    filepath = dir_path / "env_config.json"

    filepath.write_text(json.dumps({"initial": True}), encoding="utf-8")

    data = {"framework_standard": "TEST_PROTOCOL", "encoding": "UTF-8"}
    atomic_write_json(filepath, data, logger)

    content = json.loads(filepath.read_text(encoding="utf-8"))
    assert content["framework_standard"] == "TEST_PROTOCOL"

def _concurrent_writer(filepath, worker_id, iterations):
    logger = make_logger()
    for i in range(iterations):
        payload = {"worker": worker_id, "iteration": i, "status": "ACTIVE"}
        atomic_write_json(filepath, payload, logger)

def test_atomic_write_json_concurrency(tmp_path):
    logger = make_logger()
    target_file = tmp_path / "concurrent_manifest.json"
    num_workers = 4
    iterations_per_worker = 10
    threads = []

    for worker_id in range(num_workers):
        t = threading.Thread(
            target=_concurrent_writer,
            args=(target_file, worker_id, iterations_per_worker)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert target_file.exists()
