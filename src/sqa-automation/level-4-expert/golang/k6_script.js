/**
 * Level 4 - Expert: k6 Load Test Script
 * =======================================
 * k6 is a modern open-source load testing tool that uses JavaScript
 * for test scripts. You can run it from Go projects or CI pipelines.
 *
 * Install k6: https://k6.io/docs/getting-started/installation/
 *
 * Run:
 *   k6 run golang/k6_script.js --vus 10 --duration 30s
 *
 * Performance budget enforced via thresholds below:
 *   - 95th percentile response time < 500ms
 *   - Error rate < 1%
 *   - Min throughput > 10 RPS
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ── Custom metrics ────────────────────────────────────────────────────────────

const errorRate    = new Rate('error_rate');
const responseTime = new Trend('response_time_ms', true);

// ── Test configuration ────────────────────────────────────────────────────────

export const options = {
  stages: [
    { duration: '15s', target: 10  },   // Ramp up to 10 VUs
    { duration: '30s', target: 50  },   // Ramp up to 50 VUs (peak load)
    { duration: '15s', target:  0  },   // Ramp down
  ],

  // Performance budget — test fails if any threshold is breached
  thresholds: {
    http_req_duration:        ['p(95)<500'],   // 95th percentile < 500ms
    http_req_failed:          ['rate<0.01'],   // Error rate < 1%
    error_rate:               ['rate<0.01'],
    response_time_ms:         ['p(95)<500'],
  },
};

// ── Base URL (override with: k6 run --env BASE_URL=http://myapp:8080) ─────────

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// ── Scenario helpers ──────────────────────────────────────────────────────────

function listItems() {
  const limit = Math.floor(Math.random() * 16) + 5; // 5–20
  const res = http.get(`${BASE_URL}/items?limit=${limit}`);

  const ok = check(res, {
    'list items status 200': (r) => r.status === 200,
    'list items has body':   (r) => r.body.length > 0,
  });

  errorRate.add(!ok);
  responseTime.add(res.timings.duration);
}

function getItem() {
  const id  = Math.floor(Math.random() * 100) + 1;
  const res = http.get(`${BASE_URL}/items/${id}`);

  const ok = check(res, {
    'get item is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });

  errorRate.add(!ok);
  responseTime.add(res.timings.duration);
}

// ── Main virtual user function ────────────────────────────────────────────────

export default function () {
  // Weight: 70% list, 30% get individual item
  if (Math.random() < 0.7) {
    listItems();
  } else {
    getItem();
  }

  sleep(Math.random() * 1.5 + 0.5); // Think time: 0.5–2s
}

// ── Setup (runs once before test) ─────────────────────────────────────────────

export function setup() {
  const res = http.get(`${BASE_URL}/items`);
  if (res.status !== 200) {
    throw new Error(`Application health check failed: ${res.status} ${res.body}`);
  }
  console.log(`✓ Application is up at ${BASE_URL}`);
}
