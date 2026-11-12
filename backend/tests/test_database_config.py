"""Tests for PrimeCloud MySQL environment configuration."""

import pytest

from app.db.database import _database_url


def _clear_mysql_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DATABASE_URL",
        "MYSQL_URL",
        "MYSQL_HOST",
        "MYSQLHOST",
        "MYSQL_PORT",
        "MYSQLPORT",
        "MYSQL_USER",
        "MYSQLUSER",
        "MYSQL_PASSWORD",
        "MYSQLPASSWORD",
        "MYSQL_DATABASE",
        "MYSQLDATABASE",
        "APP_ENV",
    ):
        monkeypatch.delenv(name, raising=False)


def test_mysqlport_with_database_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_mysql_environment(monkeypatch)
    monkeypatch.setenv("MYSQLHOST", "mysql.internal")
    monkeypatch.setenv("MYSQLUSER", "app")
    monkeypatch.setenv("MYSQLPASSWORD", "secret")
    monkeypatch.setenv("MYSQLPORT", "3306/default")

    url = _database_url()

    assert url.drivername == "mysql+pymysql"
    assert url.host == "mysql.internal"
    assert url.port == 3306
    assert url.database == "default"


def test_explicit_mysql_database_overrides_port_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_mysql_environment(monkeypatch)
    monkeypatch.setenv("MYSQL_DATABASE", "jenga")
    monkeypatch.setenv("MYSQLPORT", "3306/default")
    monkeypatch.setenv("MYSQL_HOST", "mysql.internal")
    monkeypatch.setenv("MYSQL_USER", "app")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")

    url = _database_url()

    assert url.database == "jenga"


def test_invalid_mysql_port_reports_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_mysql_environment(monkeypatch)
    monkeypatch.setenv("MYSQL_PORT", "not-a-port/default")
    monkeypatch.setenv("MYSQL_HOST", "mysql.internal")
    monkeypatch.setenv("MYSQL_USER", "app")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")

    with pytest.raises(RuntimeError, match="Invalid MySQL port"):
        _database_url()


@pytest.mark.parametrize(
    "host_setting",
    [
        "mysql.internal:3307/default",
        "mysql://mysql.internal:3307/default",
    ],
)
def test_mysql_host_with_port_and_database_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
    host_setting: str,
) -> None:
    _clear_mysql_environment(monkeypatch)
    monkeypatch.setenv("MYSQLHOST", host_setting)
    monkeypatch.setenv("MYSQLUSER", "app")
    monkeypatch.setenv("MYSQLPASSWORD", "secret")

    url = _database_url()

    assert url.host == "mysql.internal"
    assert url.port == 3307
    assert url.database == "default"


@pytest.mark.parametrize("host_setting", ["mysql.internal/path/too/much", "a" * 64])
def test_invalid_mysql_host_fails_with_configuration_hint(
    monkeypatch: pytest.MonkeyPatch,
    host_setting: str,
) -> None:
    _clear_mysql_environment(monkeypatch)
    monkeypatch.setenv("MYSQLHOST", host_setting)
    monkeypatch.setenv("MYSQLUSER", "app")
    monkeypatch.setenv("MYSQLPASSWORD", "secret")
    monkeypatch.setenv("MYSQLDATABASE", "default")

    with pytest.raises(RuntimeError, match="MYSQL_HOST"):
        _database_url()
