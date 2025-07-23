# Performance Tests for SQL DB LLM Agent

This directory contains performance tests, profiling tools, and optimization scripts for the SQL DB LLM Agent system.

## Test Categories

The performance tests are organized into the following categories:

1. **Database Performance Tests** (`test_db_performance.py`)
   - Query execution performance
   - Connection pool performance
   - Database connector comparison (MS-SQL vs SAP HANA)

2. **API Performance Tests** (`test_api_performance.py`)
   - API endpoint response time
   - Concurrent API call performance
   - Success rate under load

3. **Memory Profiling** (`test_memory_profiling.py`)
   - Memory usage tracking
   - Memory leak detection
   - Large result set memory handling

4. **Load Testing** (`locustfile.py`)
   - Simulated user load testing
   - Scalability testing
   - System behavior under stress

5. **System Optimization** (`optimize_system.py`)
   - Performance bottleneck identification
   - Automatic optimization application
   - Optimization recommendations

## Running the Tests

You can run the performance tests using the provided `run_performance_tests.py` script:

```bash
# Run all performance tests
python -m backend.tests.performance.run_performance_tests --all

# Run specific test categories
python -m backend.tests.performance.run_performance_tests --db
python -m backend.tests.performance.run_performance_tests --api
python -m backend.tests.performance.run_performance_tests --memory
python -m backend.tests.performance.run_performance_tests --load

# Run load tests with custom parameters
python -m backend.tests.performance.run_performance_tests --load --users 100 --duration 120

# Run system optimization
python -m backend.tests.performance.run_performance_tests --optimize
```

## Test Configuration

The performance tests can be configured using the settings in `config.py`. Key configuration options include:

- Database connection settings
- Test queries of varying complexity
- Natural language test queries
- Performance thresholds
- Load test parameters

## Test Results

Test results are saved in the `backend/tests/performance/results` directory. The results include:

- Performance metrics in text and JSON formats
- Charts and visualizations
- Memory usage profiles
- Optimization recommendations

## Optimization Process

The system optimization process follows these steps:

1. Run performance tests to establish baseline metrics
2. Analyze test results to identify bottlenecks
3. Generate optimization recommendations
4. Apply optimizations automatically where possible
5. Run tests again to measure improvement
6. Generate a summary report

## Key Performance Metrics

The performance tests measure the following key metrics:

- **Response Time**: Average, median, and percentile response times
- **Throughput**: Requests per second under various loads
- **Memory Usage**: Memory consumption patterns and potential leaks
- **Success Rate**: Percentage of successful requests under load
- **Database Performance**: Query execution time and resource usage

## Best Practices

When running performance tests:

1. Ensure the system is in a clean state before testing
2. Run tests multiple times to get consistent results
3. Test with realistic data volumes and user loads
4. Compare results against established performance thresholds
5. Document all optimizations and their impact