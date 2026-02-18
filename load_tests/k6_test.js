/**
 * k6 Load Test for LLM Ranking Service
 * Author: Gopi Krishna Vajrala
 *
 * Usage:
 *   k6 run load_tests/k6_test.js
 *
 * Targets:
 *   - p95 latency < 120ms
 *   - 5,000 RPS sustained
 *   - Error rate < 0.1%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const rankingLatency = new Trend('ranking_latency', true);
const successCount = new Counter('successful_requests');

// Test configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-api-key';

// Load test stages
export const options = {
  stages: [
    // Warm-up
    { duration: '30s', target: 100 },
    // Ramp up to target
    { duration: '1m', target: 500 },
    // Sustained load
    { duration: '3m', target: 1000 },
    // Peak load (5000 RPS target)
    { duration: '2m', target: 2500 },
    // Cool down
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    'http_req_duration{name:rank}': ['p(95)<120'],  // p95 < 120ms
    'errors': ['rate<0.01'],                         // Error rate < 1%
    'ranking_latency': ['p(50)<50', 'p(95)<120', 'p(99)<200'],
  },
};

// Sample data
const TITLES = [
  'Breaking News: AI Revolution in Healthcare',
  'Top 10 Machine Learning Frameworks',
  'How to Build Scalable Microservices',
  'Climate Change: Latest Findings',
  'Stock Market: Tech Sector Surge',
  'Guide to Cloud-Native Architecture',
  'Sports Update: Championship Results',
  'Cybersecurity Best Practices',
  'Remote Work Productivity Tips',
  'Electric Vehicles: Market Trends',
];

const CONTEXTS = [
  { location: 'US', device: 'mobile', time_of_day: 'morning' },
  { location: 'UK', device: 'desktop', time_of_day: 'afternoon' },
  { location: 'IN', device: 'tablet', time_of_day: 'evening' },
];

function getRandomTitles(min, max) {
  const count = Math.floor(Math.random() * (max - min + 1)) + min;
  const shuffled = [...TITLES].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

export default function () {
  const userId = `user_${Math.floor(Math.random() * 100000)}`;
  const context = CONTEXTS[Math.floor(Math.random() * CONTEXTS.length)];
  const titles = getRandomTitles(3, 10);

  const payload = JSON.stringify({
    user_id: userId,
    context: context,
    candidate_titles: titles,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    tags: { name: 'rank' },
  };

  const res = http.post(`${BASE_URL}/rank`, payload, params);

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'has ranked_titles': (r) => {
      try {
        return JSON.parse(r.body).ranked_titles !== undefined;
      } catch {
        return false;
      }
    },
    'has model_version': (r) => {
      try {
        return JSON.parse(r.body).model_version !== undefined;
      } catch {
        return false;
      }
    },
    'latency under 120ms': (r) => r.timings.duration < 120,
  });

  errorRate.add(!success);
  rankingLatency.add(res.timings.duration);
  if (success) successCount.add(1);

  sleep(0.01);
}

// Health check scenario
export function healthCheck() {
  const res = http.get(`${BASE_URL}/health`);
  check(res, {
    'health check OK': (r) => r.status === 200,
  });
}
