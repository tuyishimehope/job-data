from dataclasses import dataclass, field
from time import perf_counter
from uuid import uuid4


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    parent_span_id: str | None = None

    start_time: float = field(
        default_factory=perf_counter
    )

    end_time: float | None = None

    def finish(self) -> None:
        self.end_time = perf_counter()

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None

        return (
            self.end_time - self.start_time
        ) * 1000