import sys


def test_python_version_is_pinned():
    assert sys.version_info[:2] == (3, 12)


def test_engine_package_imports():
    import hexcoach.engine  # noqa: F401
