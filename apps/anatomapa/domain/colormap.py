from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ColorMap:
    """Piecewise linear colormap defined by control points.

    Parameters
    ----------
    stops:
        Sequence of (t, (r, g, b)) where t is in [0, 1] and the RGB values are
        in [0, 255]. Must be sorted by t and include both t=0.0 and t=1.0.
    """

    stops: tuple[tuple[float, tuple[int, int, int]], ...]

    def color_at(self, t: float) -> tuple[int, int, int]:
        """Return the interpolated RGB colour for a value t in [0, 1].

        Values outside [0, 1] are clamped to the range.
        """
        t = max(0.0, min(1.0, t))

        if len(self.stops) == 1:
            return self.stops[0][1]

        lo_t, lo_rgb = self.stops[0]
        hi_t, hi_rgb = self.stops[-1]

        for i in range(len(self.stops) - 1):
            a_t, a_rgb = self.stops[i]
            b_t, b_rgb = self.stops[i + 1]
            if a_t <= t <= b_t:
                lo_t, lo_rgb = a_t, a_rgb
                hi_t, hi_rgb = b_t, b_rgb
                break

        span = hi_t - lo_t
        if span == 0.0:
            return lo_rgb

        ratio = (t - lo_t) / span
        r = round(lo_rgb[0] + ratio * (hi_rgb[0] - lo_rgb[0]))
        g = round(lo_rgb[1] + ratio * (hi_rgb[1] - lo_rgb[1]))
        b = round(lo_rgb[2] + ratio * (hi_rgb[2] - lo_rgb[2]))
        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        )
