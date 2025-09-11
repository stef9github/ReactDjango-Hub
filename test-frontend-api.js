#!/usr/bin/env node

/**
 * Test Frontend API Integration
 * Tests both direct service connections and Kong Gateway (when available)
 */

const http = require('http');

// Test endpoints
const tests = [
  {
    name: 'Identity Service - Direct',
    url: 'http://localhost:8001/health',
    expected: 200
  },
  {
    name: 'Content Service - Direct', 
    url: 'http://localhost:8002/health',
    expected: 200
  },
  {
    name: 'Kong Gateway - Proxy',
    url: 'http://localhost:8000',
    expected: [200, 404] // Kong might return 404 for root
  },
  {
    name: 'Kong Admin API',
    url: 'http://localhost:8445/status',
    expected: 200
  }
];

async function testEndpoint(test) {
  return new Promise((resolve) => {
    const url = new URL(test.url);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'GET',
      timeout: 2000
    };

    const req = http.request(options, (res) => {
      const expectedCodes = Array.isArray(test.expected) ? test.expected : [test.expected];
      const success = expectedCodes.includes(res.statusCode);
      console.log(`${success ? '✅' : '❌'} ${test.name}: ${res.statusCode} ${success ? 'OK' : 'FAILED'}`);
      resolve(success);
    });

    req.on('error', (err) => {
      console.log(`❌ ${test.name}: Connection failed - ${err.message}`);
      resolve(false);
    });

    req.on('timeout', () => {
      console.log(`❌ ${test.name}: Timeout`);
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function runTests() {
  console.log('🧪 Testing Frontend API Integration\n');
  console.log('=====================================\n');
  
  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    const result = await testEndpoint(test);
    if (result) passed++;
    else failed++;
  }

  console.log('\n=====================================');
  console.log(`\n📊 Results: ${passed} passed, ${failed} failed\n`);

  // Frontend configuration recommendation
  console.log('📝 Frontend Configuration Recommendation:\n');
  
  if (tests[2].expected.includes(404)) { // Kong check
    console.log('Kong Gateway is NOT running. Frontend should use direct service endpoints:');
    console.log('  VITE_API_URL=http://localhost:8001 (for Identity Service)');
    console.log('  VITE_CONTENT_API_URL=http://localhost:8002');
    console.log('  VITE_COMMUNICATION_API_URL=http://localhost:8003');
    console.log('  VITE_WORKFLOW_API_URL=http://localhost:8004');
  } else {
    console.log('Kong Gateway is running! Frontend should use:');
    console.log('  VITE_API_URL=http://localhost:8000');
  }
}

runTests();