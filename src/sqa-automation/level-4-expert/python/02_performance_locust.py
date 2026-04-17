"""
Level 4 - Expert: Performance / Load Testing with Locust
=========================================================
Locust simulates concurrent virtual users sending HTTP requests
to your application and measures throughput, latency, and error rates.

Prerequisites:
    pip install locust fastapi uvicorn

Usage:
    # 1. Start the app (in a separate terminal):
    #    uvicorn 02_performance_locust:app --port 8000

    # 2a. Interactive web UI:
    #    locust -f 02_performance_locust.py --host http://localhost:8000

    # 2b. Headless CI mode:
    #    locust -f 02_performance_locust.py --headless \\
    #           --users 50 --spawn-rate 10 --run-time 60s \\
    #           --host http://localhost:8000 --html report.html

Performance budget (adjust to your SLA):
    - p95 response time  < 500 ms
    - Error rate          < 1 %
    - Throughput          > 100 RPS
"""

import random
from locust import HttpUser, TaskSet, task, between, events
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import time


# ─── Sample FastAPI app (System Under Test) ───────────────────────────────────

app = FastAPI()

_items: dict[int, dict] = {
    i: {"id": i, "name": f"Item {i}", "price": round(random.uniform(1.0, 100.0), 2)}
    for i in range(1, 101)
}


@app.get("/items")
def list_items(limit: int = 20):
    return list(_items.values())[:limit]


@app.get("/items/{item_id}")
def get_item(item_id: int):
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/items")
def create_item(item: dict):
    new_id = max(_items.keys()) + 1
    _items[new_id] = {"id": new_id, **item}
    return JSONResponse(status_code=201, content=_items[new_id])


# ─── Locust User Behaviour ────────────────────────────────────────────────────

class ItemBrowsingBehaviour(TaskSet):
    """Simulates a user browsing the item catalogue."""

    @task(5)
    def list_items(self):
        """Most common action: listing items (weight 5)."""
        limit = random.randint(5, 20)
        with self.client.get(f"/items?limit={limit}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected 200, got {response.status_code}")

    @task(3)
    def get_specific_item(self):
        """Get a specific item by ID (weight 3)."""
        item_id = random.randint(1, 100)
        with self.client.get(f"/items/{item_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 404 is an expected outcome for some IDs
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def get_nonexistent_item(self):
        """Verify error handling under load (weight 1)."""
        with self.client.get("/items/99999", catch_response=True) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got {response.status_code}")


class ItemAPIUser(HttpUser):
    """
    Simulates a typical API user.
    wait_time: pause between tasks (simulates think time).
    """
    tasks = [ItemBrowsingBehaviour]
    wait_time = between(0.5, 2.0)


# ─── Custom event hooks for CI assertions ─────────────────────────────────────

@events.quitting.add_listener
def assert_performance_budget(environment, **_kwargs):
    """
    Fail the Locust run if the performance budget is exceeded.
    This causes a non-zero exit code in CI.
    """
    stats = environment.runner.stats.total
    fail = False

    if stats.fail_ratio > 0.01:
        print(f"[FAIL] Error rate {stats.fail_ratio:.1%} exceeds budget of 1%")
        fail = True

    if stats.avg_response_time > 500:
        print(f"[FAIL] Average response time {stats.avg_response_time:.0f}ms exceeds 500ms budget")
        fail = True

    if fail:
        environment.process_exit_code = 1
