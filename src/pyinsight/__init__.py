"""Public package interface for pyinsight."""

from pyinsight.decorators import slow, trace
from pyinsight.runtime import configure
from pyinsight.spans import span

__all__ = ["configure", "slow", "span", "trace"]
