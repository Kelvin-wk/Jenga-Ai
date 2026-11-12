"""Tests for database startup retries and failure handling."""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

import app.db.database as database
import app.main as main


def _connection_error() -> OperationalError:
    return OperationalError("SELECT 1", {}, RuntimeError("private-host supersecret"))


def test_init_db_retries_operational_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0
    delays: list[float] = []

    def initialize_once() -> None:
        nonlocal attempts
        attempts += 1
        if attempts < database.DB_INIT_MAX_ATTEMPTS:
            raise _connection_error()

    monkeypatch.setattr(database, "_initialize_database_once", initialize_once)
    monkeypatch.setattr(database.time, "sleep", delays.append)

    database.init_db()

    assert attempts == database.DB_INIT_MAX_ATTEMPTS
    assert delays == list(database.DB_INIT_RETRY_DELAYS_SECONDS)


def test_init_db_logs_safely_and_raises_after_retries(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_initialization() -> None:
        raise _connection_error()

    monkeypatch.setattr(database, "_initialize_database_once", fail_initialization)
    monkeypatch.setattr(database.time, "sleep", lambda _: None)

    with caplog.at_level(logging.WARNING, logger=database.__name__):
        with pytest.raises(OperationalError):
            database.init_db()

    assert f"failed after {database.DB_INIT_MAX_ATTEMPTS} attempts" in caplog.text
    assert "private-host" not in caplog.text
    assert "supersecret" not in caplog.text


def test_startup_does_not_continue_when_database_initialization_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_initialization() -> None:
        raise _connection_error()

    monkeypatch.setattr(main, "init_db", fail_initialization)

    with pytest.raises(OperationalError):
        with TestClient(main.app):
            pass
