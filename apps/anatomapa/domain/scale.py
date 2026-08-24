from __future__ import annotations

import math
from typing import Protocol, runtime_checkable


@runtime_checkable
class Scale(Protocol):
    """Protocol for value normalisation strategies."""

    def normalize(self, values: list[float]) -> list[float]:
        """Normalise values into the [0, 1] range."""
        ...


class LinearScale:
    """Linear min-max normalisation."""

    def normalize(self, values: list[float]) -> list[float]:
        """Map values to [0, 1] using a min-max scale.

        Inputs whose values are all equal map to 0.0.
        """
        if not values:
            return []
        lo = min(values)
        hi = max(values)
        if hi == lo:
            return [0.0] * len(values)
        span = hi - lo
        return [(v - lo) / span for v in values]


class LogScale:
    """log1p min-max normalisation, safe for zeros and negative values."""

    def normalize(self, values: list[float]) -> list[float]:
        """Map values to [0, 1] using log1p followed by a min-max scale.

        Negative values are shifted so that the minimum maps to log1p(0).
        """
        if not values:
            return []

        # Desloca para garantir que todos os valores sejam >= 0 antes do log1p
        lo_raw = min(values)
        shift = max(0.0, -lo_raw)
        shifted = [v + shift for v in values]

        logged = [math.log1p(v) for v in shifted]

        lo = min(logged)
        hi = max(logged)
        if hi == lo:
            return [0.0] * len(logged)

        span = hi - lo
        return [(v - lo) / span for v in logged]
