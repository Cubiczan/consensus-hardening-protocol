"""Optional resilience layer.

The full implementation lives in ``cubiczan-resilience`` and is pulled in by the
``resilience`` extra. When it is absent this module supplies a dependency-free
fallback so the package installs from PyPI with no third-party requirements.

The fallback honours ``max_attempts``, ``base_delay`` and ``multiplier``. It does
NOT enforce ``timeout`` — bounding an arbitrary call without threads is not
portable, so a caller that needs a hard deadline should install the extra.
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

try:  # pragma: no cover - exercised only when the extra is installed
    from cubiczan_resilience import atomic_write, resilient  # type: ignore

    HAVE_FULL_RESILIENCE = True
except ImportError:
    HAVE_FULL_RESILIENCE = False

    def resilient(  # type: ignore[misc]
        func: F | None = None,
        *,
        timeout: float = 30.0,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        multiplier: float = 2.0,
        **_ignored: Any,
    ) -> Any:
        """Retry a callable with exponential backoff. See module docstring."""

        def decorate(fn: F) -> F:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                delay = base_delay
                for attempt in range(1, max_attempts + 1):
                    try:
                        return fn(*args, **kwargs)
                    except Exception:
                        if attempt == max_attempts:
                            raise
                        time.sleep(delay)
                        delay *= multiplier
                raise AssertionError("unreachable")

            return wrapper  # type: ignore[return-value]

        return decorate(func) if callable(func) else decorate

    def atomic_write(path: Any, data: str, **_ignored: Any) -> None:  # type: ignore[misc]
        """Write via a temp file then replace, so readers never see a partial file."""
        import os
        import tempfile

        path = str(path)
        d = os.path.dirname(path) or "."
        fd, tmp = tempfile.mkstemp(dir=d)
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(data)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


__all__ = ["resilient", "atomic_write", "HAVE_FULL_RESILIENCE"]
