# Performance Review Checklist

## Database Performance
- [ ] Queries use appropriate indexes
- [ ] N+1 query problems eliminated
- [ ] Database connection pooling configured
- [ ] Query pagination implemented for large datasets
- [ ] Proper use of eager loading (select_related/prefetch_related)
- [ ] Database query optimization (EXPLAIN analyzed)
- [ ] Unnecessary JOINs avoided
- [ ] Batch operations used where appropriate
- [ ] Database caching layer implemented
- [ ] Read replicas utilized for read-heavy operations

## Caching Strategy
- [ ] Redis/Memcached properly configured
- [ ] Cache invalidation strategy defined
- [ ] Cache key naming conventions followed
- [ ] TTL values appropriately set
- [ ] Cache warming implemented where needed
- [ ] CDN configured for static assets
- [ ] Browser caching headers set correctly
- [ ] Database query results cached
- [ ] API response caching implemented
- [ ] Session storage optimized

## Frontend Performance
- [ ] Bundle size optimized (<500KB initial load)
- [ ] Code splitting implemented
- [ ] Lazy loading for routes and components
- [ ] Images optimized and using modern formats (WebP)
- [ ] Critical CSS inlined
- [ ] JavaScript minified and compressed
- [ ] Tree shaking removing unused code
- [ ] Web fonts optimized
- [ ] Service worker for offline capability
- [ ] Preconnect/prefetch for critical resources

## React-Specific Optimizations
- [ ] React.memo used for expensive components
- [ ] useMemo/useCallback preventing unnecessary re-renders
- [ ] Virtual scrolling for long lists
- [ ] Debouncing/throttling for frequent events
- [ ] Component lazy loading with Suspense
- [ ] State updates batched appropriately
- [ ] Context providers split to minimize re-renders
- [ ] Keys properly used in lists
- [ ] Production build optimizations enabled
- [ ] DevTools profiler shows acceptable performance

## API Performance
- [ ] Response times <200ms for critical endpoints
- [ ] Payload sizes minimized
- [ ] Compression enabled (gzip/brotli)
- [ ] Pagination implemented
- [ ] Field filtering available
- [ ] Batch endpoints for multiple operations
- [ ] GraphQL query complexity limited
- [ ] WebSocket used for real-time data
- [ ] Long polling avoided where possible
- [ ] Connection keep-alive configured

## Async Processing
- [ ] Long-running tasks moved to background jobs
- [ ] Message queue (Celery/RabbitMQ) properly configured
- [ ] Task priorities implemented
- [ ] Task retries configured
- [ ] Dead letter queues for failed tasks
- [ ] Task result backend optimized
- [ ] Batch processing for bulk operations
- [ ] Rate limiting for resource-intensive tasks
- [ ] Task monitoring and alerting
- [ ] Graceful shutdown handling

## Memory Management
- [ ] Memory leaks identified and fixed
- [ ] Large objects properly garbage collected
- [ ] Streaming used for large file operations
- [ ] Memory profiling performed
- [ ] Object pooling for frequently created objects
- [ ] Weak references used where appropriate
- [ ] Memory limits configured
- [ ] OOM killer properly configured
- [ ] Memory usage monitoring
- [ ] Heap dumps analyzed

## Network Optimization
- [ ] HTTP/2 or HTTP/3 enabled
- [ ] Keep-alive connections configured
- [ ] DNS prefetching implemented
- [ ] Reduced number of domains
- [ ] Minimized redirect chains
- [ ] API calls batched where possible
- [ ] WebSocket connection pooling
- [ ] Appropriate timeout values
- [ ] Retry logic with exponential backoff
- [ ] Circuit breakers implemented

## Load Testing Results
- [ ] Load testing performed
- [ ] Response times under load acceptable
- [ ] Throughput meets requirements
- [ ] Error rate <1% under normal load
- [ ] Resource utilization acceptable
- [ ] Scaling limits identified
- [ ] Bottlenecks documented
- [ ] Performance regression tests
- [ ] Stress testing completed
- [ ] Capacity planning documented

## Monitoring & Metrics
- [ ] APM tools configured (New Relic/DataDog)
- [ ] Custom performance metrics tracked
- [ ] Real User Monitoring (RUM) enabled
- [ ] Synthetic monitoring configured
- [ ] Alert thresholds defined
- [ ] Performance budgets set
- [ ] Core Web Vitals monitored
- [ ] Database slow query log enabled
- [ ] Performance dashboards created
- [ ] SLA/SLO targets defined

## Resource Optimization
- [ ] CPU usage optimized
- [ ] Memory usage within limits
- [ ] Disk I/O minimized
- [ ] Network bandwidth optimized
- [ ] Container resources properly limited
- [ ] Auto-scaling configured
- [ ] Resource pooling implemented
- [ ] Idle resource cleanup
- [ ] Resource contention avoided
- [ ] Cost optimization considered

## Algorithm Efficiency
- [ ] Time complexity analyzed (O notation)
- [ ] Space complexity optimized
- [ ] Appropriate data structures used
- [ ] Sorting algorithms optimal
- [ ] Search algorithms efficient
- [ ] Recursive algorithms have base cases
- [ ] Dynamic programming used where beneficial
- [ ] Memoization implemented
- [ ] Parallel processing utilized
- [ ] SIMD operations where applicable

## Build & Deploy Performance
- [ ] Build times optimized
- [ ] Incremental builds configured
- [ ] Build caching implemented
- [ ] Parallel build processes
- [ ] Docker layer caching
- [ ] CI/CD pipeline optimized
- [ ] Deployment rollout strategy
- [ ] Zero-downtime deployments
- [ ] Rollback capability tested
- [ ] Asset precompilation

## Mobile Performance
- [ ] Mobile-first responsive design
- [ ] Touch events optimized
- [ ] Viewport meta tag configured
- [ ] Reduced JavaScript for mobile
- [ ] Adaptive image serving
- [ ] Offline capability
- [ ] Battery usage considered
- [ ] Network awareness implemented
- [ ] Progressive Web App features
- [ ] App shell architecture

## Performance Culture
- [ ] Performance budgets enforced
- [ ] Regular performance reviews
- [ ] Performance regression prevention
- [ ] Team training on performance
- [ ] Performance documentation
- [ ] Performance testing automated
- [ ] Performance metrics visible
- [ ] Post-mortems for performance issues
- [ ] Performance champions identified
- [ ] Continuous improvement process