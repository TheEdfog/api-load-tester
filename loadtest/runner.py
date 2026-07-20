from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable

import aiohttp

from loadtest.models import LoadConfig, Observation


def rate_for_second(config: LoadConfig, second: int) -> float:
    """Return the target RPS for a zero-based one-second bucket."""
    if config.duration == 1:
        return config.final_rate
    progress = second / (config.duration - 1)
    return config.start_rate + (config.final_rate - config.start_rate) * progress


async def _send_request(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    config: LoadConfig,
) -> Observation:
    started = time.perf_counter()
    try:
        async with (
            semaphore,
            session.request(
                config.method,
                config.url,
                headers=config.headers,
                json=config.json_body,
            ) as response,
        ):
            await response.read()
            return Observation(time.perf_counter() - started, response.status)
    except TimeoutError:
        return Observation(time.perf_counter() - started, None, "timeout")
    except aiohttp.ClientError as exc:
        return Observation(time.perf_counter() - started, None, type(exc).__name__)


async def run_load_test(config: LoadConfig) -> tuple[list[Observation], float]:
    """Schedule requests and return observations plus total wall-clock duration."""
    timeout = aiohttp.ClientTimeout(total=config.timeout)
    connector = aiohttp.TCPConnector(limit=config.concurrency)
    semaphore = asyncio.Semaphore(config.concurrency)
    tasks: list[Awaitable[Observation]] = []
    wall_started = time.perf_counter()

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        for second in range(config.duration):
            bucket_started = wall_started + second
            rate = rate_for_second(config, second)
            request_count = max(1, round(rate))

            for index in range(request_count):
                scheduled_at = bucket_started + index / rate
                delay = scheduled_at - time.perf_counter()
                if delay > 0:
                    await asyncio.sleep(delay)
                tasks.append(asyncio.create_task(_send_request(session, semaphore, config)))

        observations = await asyncio.gather(*tasks)

    return observations, time.perf_counter() - wall_started
