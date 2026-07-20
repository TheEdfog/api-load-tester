from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LoadConfig:
    url: str
    method: str = "GET"
    start_rate: float = 10.0
    end_rate: float | None = None
    duration: int = 10
    concurrency: int = 100
    timeout: float = 10.0
    headers: dict[str, str] = field(default_factory=dict)
    json_body: Any | None = None

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        if self.start_rate <= 0:
            raise ValueError("start_rate must be greater than zero")
        if self.end_rate is not None and self.end_rate <= 0:
            raise ValueError("end_rate must be greater than zero")
        if self.duration <= 0:
            raise ValueError("duration must be greater than zero")
        if self.concurrency <= 0:
            raise ValueError("concurrency must be greater than zero")
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")

    @property
    def final_rate(self) -> float:
        return self.end_rate if self.end_rate is not None else self.start_rate


@dataclass(frozen=True, slots=True)
class Observation:
    latency_seconds: float
    status: int | None
    error: str | None = None

    @property
    def successful(self) -> bool:
        return self.status is not None and 200 <= self.status < 400 and self.error is None
