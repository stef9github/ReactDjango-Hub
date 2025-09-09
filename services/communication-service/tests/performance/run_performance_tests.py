#!/usr/bin/env python3
"""
Performance Test Runner for Communication Service
Comprehensive performance testing including benchmarks, load testing, and monitoring
"""

import os
import sys
import time
import json
import argparse
import subprocess
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor


class PerformanceTestRunner:
    """Comprehensive performance test runner and analyzer"""
    
    def __init__(self, service_url: str = "http://localhost:8002"):
        self.service_url = service_url
        self.results_dir = Path("performance_results")
        self.results_dir.mkdir(exist_ok=True)
        self.test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_all_performance_tests(self) -> Dict:
        """Run comprehensive performance test suite"""
        print("🚀 Starting Communication Service Performance Test Suite")
        print(f"⏰ Test timestamp: {self.test_timestamp}")
        print(f"🎯 Target service: {self.service_url}")
        print("=" * 60)
        
        results = {
            "timestamp": self.test_timestamp,
            "service_url": self.service_url,
            "system_info": self.get_system_info(),
            "tests": {}
        }
        
        # 1. Unit performance tests
        print("\n📊 Running unit performance tests...")
        results["tests"]["unit_performance"] = self.run_unit_performance_tests()
        
        # 2. API endpoint benchmarks
        print("\n🌐 Running API endpoint benchmarks...")
        results["tests"]["api_benchmarks"] = self.run_api_benchmarks()
        
        # 3. Database performance tests
        print("\n🗄️ Running database performance tests...")
        results["tests"]["database_performance"] = self.run_database_performance_tests()
        
        # 4. Queue performance tests
        print("\n📬 Running queue performance tests...")
        results["tests"]["queue_performance"] = self.run_queue_performance_tests()
        
        # 5. Load testing with Locust
        print("\n🔥 Running load tests...")
        results["tests"]["load_testing"] = self.run_load_tests()
        
        # 6. Memory and resource monitoring
        print("\n💾 Running memory and resource tests...")
        results["tests"]["resource_monitoring"] = self.run_resource_tests()
        
        # 7. Generate performance report
        print("\n📈 Generating performance report...")
        self.generate_performance_report(results)
        
        print(f"\n✅ Performance testing complete! Results saved to {self.results_dir}")
        return results
    
    def get_system_info(self) -> Dict:
        """Collect system information for performance context"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
            "memory_available": psutil.virtual_memory().available / (1024**3),  # GB
            "python_version": sys.version,
            "platform": sys.platform
        }
    
    def run_unit_performance_tests(self) -> Dict:
        """Run pytest-based performance tests"""
        try:
            # Run performance-marked tests
            cmd = [
                "pytest", 
                "tests/performance/test_load_testing.py",
                "-m", "performance",
                "-v",
                "--tb=short",
                "--benchmark-json=performance_results/benchmark_results.json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": "5m"  # Approximate
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_api_benchmarks(self) -> Dict:
        """Benchmark API endpoint performance"""
        import httpx
        
        endpoints = [
            {
                "name": "health_check",
                "method": "GET",
                "url": "/health",
                "auth_required": False
            },
            {
                "name": "metrics",
                "method": "GET", 
                "url": "/metrics",
                "auth_required": False
            },
            {
                "name": "send_notification",
                "method": "POST",
                "url": "/api/v1/notifications",
                "auth_required": True,
                "data": {
                    "type": "email",
                    "to": "benchmark@example.com",
                    "subject": "Benchmark Test",
                    "message": "API benchmark testing"
                }
            }
        ]
        
        results = {}
        headers = {"Authorization": "Bearer benchmark.test.token"}
        
        for endpoint in endpoints:
            print(f"  📍 Benchmarking {endpoint['name']}...")
            
            response_times = []
            success_count = 0
            
            try:
                with httpx.Client(base_url=self.service_url, timeout=10.0) as client:
                    for i in range(20):  # 20 requests per endpoint
                        start_time = time.time()
                        
                        if endpoint["method"] == "GET":
                            response = client.get(
                                endpoint["url"],
                                headers=headers if endpoint["auth_required"] else None
                            )
                        else:  # POST
                            response = client.post(
                                endpoint["url"],
                                json=endpoint.get("data", {}),
                                headers=headers if endpoint["auth_required"] else None
                            )
                        
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        
                        if response.status_code < 400:
                            success_count += 1
                
                results[endpoint["name"]] = {
                    "avg_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "p95_response_time": statistics.quantiles(response_times, n=20)[18],
                    "success_rate": success_count / len(response_times) * 100,
                    "total_requests": len(response_times)
                }
                
            except Exception as e:
                results[endpoint["name"]] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        return results
    
    def run_database_performance_tests(self) -> Dict:
        """Run database-specific performance tests"""
        try:
            cmd = [
                "pytest",
                "tests/performance/test_load_testing.py::TestDatabasePerformance",
                "-v",
                "--tb=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "summary": "Database performance tests completed",
                "details": result.stdout
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_queue_performance_tests(self) -> Dict:
        """Run Celery queue performance tests"""
        try:
            cmd = [
                "pytest",
                "tests/performance/test_load_testing.py::TestCeleryQueuePerformance",
                "-v",
                "--tb=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "summary": "Queue performance tests completed",
                "details": result.stdout
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def run_load_tests(self) -> Dict:
        """Run Locust-based load testing"""
        load_test_results = {}
        
        test_scenarios = [
            {
                "name": "baseline_load",
                "users": 10,
                "spawn_rate": 2,
                "duration": "2m",
                "description": "Baseline load test"
            },
            {
                "name": "moderate_load", 
                "users": 50,
                "spawn_rate": 5,
                "duration": "3m",
                "description": "Moderate load test"
            },
            {
                "name": "spike_test",
                "users": 100,
                "spawn_rate": 25,
                "duration": "1m",
                "description": "Spike load test"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  🔥 Running {scenario['name']} ({scenario['description']})...")
            
            try:
                cmd = [
                    "locust",
                    "-f", "tests/performance/locustfile.py",
                    "--host", self.service_url,
                    "--users", str(scenario["users"]),
                    "--spawn-rate", str(scenario["spawn_rate"]),
                    "-t", scenario["duration"],
                    "--headless",
                    "--csv", f"performance_results/{scenario['name']}_{self.test_timestamp}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                load_test_results[scenario["name"]] = {
                    "status": "completed" if result.returncode == 0 else "failed",
                    "exit_code": result.returncode,
                    "users": scenario["users"],
                    "spawn_rate": scenario["spawn_rate"],
                    "duration": scenario["duration"],
                    "output": result.stdout
                }
                
                # Parse CSV results if available
                csv_file = Path(f"performance_results/{scenario['name']}_{self.test_timestamp}_stats.csv")
                if csv_file.exists():
                    load_test_results[scenario["name"]]["csv_results"] = str(csv_file)
                
            except Exception as e:
                load_test_results[scenario["name"]] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return load_test_results
    
    def run_resource_tests(self) -> Dict:
        """Monitor resource usage during performance tests"""
        # Start monitoring
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        # Wait a bit to measure baseline
        time.sleep(2)
        
        # Measure resource usage
        memory_samples = []
        cpu_samples = []
        
        for _ in range(30):  # Sample for 30 seconds
            memory_samples.append(process.memory_info().rss / 1024 / 1024)
            cpu_samples.append(process.cpu_percent())
            time.sleep(1)
        
        return {
            "initial_memory_mb": initial_memory,
            "avg_memory_mb": statistics.mean(memory_samples),
            "max_memory_mb": max(memory_samples),
            "memory_growth_mb": max(memory_samples) - initial_memory,
            "avg_cpu_percent": statistics.mean(cpu_samples),
            "max_cpu_percent": max(cpu_samples),
            "monitoring_duration": "30s"
        }
    
    def generate_performance_report(self, results: Dict) -> None:
        """Generate comprehensive performance report"""
        report_file = self.results_dir / f"performance_report_{self.test_timestamp}.json"
        
        # Save detailed results
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate summary report
        summary_file = self.results_dir / f"performance_summary_{self.test_timestamp}.md"
        
        with open(summary_file, 'w') as f:
            f.write(f"# Communication Service Performance Report\n\n")
            f.write(f"**Generated:** {results['timestamp']}\n")
            f.write(f"**Service URL:** {results['service_url']}\n\n")
            
            # System info
            f.write("## System Information\n\n")
            sys_info = results['system_info']
            f.write(f"- **CPU Cores:** {sys_info['cpu_count']}\n")
            f.write(f"- **Memory Total:** {sys_info['memory_total']:.1f} GB\n")
            f.write(f"- **Memory Available:** {sys_info['memory_available']:.1f} GB\n")
            f.write(f"- **Python Version:** {sys_info['python_version']}\n\n")
            
            # API benchmarks
            if 'api_benchmarks' in results['tests']:
                f.write("## API Performance Benchmarks\n\n")
                for endpoint, metrics in results['tests']['api_benchmarks'].items():
                    if 'avg_response_time' in metrics:
                        f.write(f"### {endpoint}\n")
                        f.write(f"- **Average Response Time:** {metrics['avg_response_time']:.3f}s\n")
                        f.write(f"- **95th Percentile:** {metrics['p95_response_time']:.3f}s\n")
                        f.write(f"- **Success Rate:** {metrics['success_rate']:.1f}%\n\n")
            
            # Load test results
            if 'load_testing' in results['tests']:
                f.write("## Load Testing Results\n\n")
                for test_name, test_results in results['tests']['load_testing'].items():
                    if test_results['status'] == 'completed':
                        f.write(f"### {test_name}\n")
                        f.write(f"- **Users:** {test_results['users']}\n")
                        f.write(f"- **Duration:** {test_results['duration']}\n")
                        f.write(f"- **Status:** ✅ {test_results['status']}\n\n")
            
            # Resource monitoring
            if 'resource_monitoring' in results['tests']:
                f.write("## Resource Monitoring\n\n")
                res_mon = results['tests']['resource_monitoring']
                f.write(f"- **Average Memory Usage:** {res_mon['avg_memory_mb']:.1f} MB\n")
                f.write(f"- **Peak Memory Usage:** {res_mon['max_memory_mb']:.1f} MB\n")
                f.write(f"- **Memory Growth:** {res_mon['memory_growth_mb']:.1f} MB\n")
                f.write(f"- **Average CPU Usage:** {res_mon['avg_cpu_percent']:.1f}%\n\n")
            
            # Performance recommendations
            f.write("## Performance Recommendations\n\n")
            f.write(self.generate_recommendations(results))
        
        print(f"  📄 Detailed report: {report_file}")
        print(f"  📋 Summary report: {summary_file}")
    
    def generate_recommendations(self, results: Dict) -> str:
        """Generate performance recommendations based on test results"""
        recommendations = []
        
        # Check API performance
        if 'api_benchmarks' in results['tests']:
            for endpoint, metrics in results['tests']['api_benchmarks'].items():
                if isinstance(metrics, dict) and 'avg_response_time' in metrics:
                    if metrics['avg_response_time'] > 0.5:
                        recommendations.append(
                            f"⚠️ **{endpoint}** response time is high ({metrics['avg_response_time']:.3f}s). "
                            "Consider optimization or caching."
                        )
                    if metrics['success_rate'] < 95:
                        recommendations.append(
                            f"🚨 **{endpoint}** success rate is low ({metrics['success_rate']:.1f}%). "
                            "Investigate error handling and stability."
                        )
        
        # Check resource usage
        if 'resource_monitoring' in results['tests']:
            res_mon = results['tests']['resource_monitoring']
            if res_mon['memory_growth_mb'] > 50:
                recommendations.append(
                    f"💾 High memory growth detected ({res_mon['memory_growth_mb']:.1f} MB). "
                    "Check for memory leaks."
                )
            if res_mon['max_cpu_percent'] > 80:
                recommendations.append(
                    f"🔥 High CPU usage detected ({res_mon['max_cpu_percent']:.1f}%). "
                    "Consider performance optimization."
                )
        
        if not recommendations:
            recommendations.append("✅ All performance metrics are within acceptable ranges.")
        
        return "\n".join([f"- {rec}" for rec in recommendations])


def main():
    """Main performance testing entry point"""
    parser = argparse.ArgumentParser(description="Communication Service Performance Testing")
    parser.add_argument(
        "--service-url", 
        default="http://localhost:8002",
        help="URL of the communication service to test"
    )
    parser.add_argument(
        "--test-type",
        choices=["all", "unit", "api", "load", "database", "queue", "resources"],
        default="all",
        help="Type of performance tests to run"
    )
    parser.add_argument(
        "--output-dir",
        default="performance_results",
        help="Directory to store performance test results"
    )
    
    args = parser.parse_args()
    
    # Create performance test runner
    runner = PerformanceTestRunner(service_url=args.service_url)
    runner.results_dir = Path(args.output_dir)
    runner.results_dir.mkdir(exist_ok=True)
    
    # Run selected tests
    if args.test_type == "all":
        results = runner.run_all_performance_tests()
    else:
        # Run specific test type
        print(f"🎯 Running {args.test_type} performance tests...")
        if args.test_type == "unit":
            results = {"unit_performance": runner.run_unit_performance_tests()}
        elif args.test_type == "api":
            results = {"api_benchmarks": runner.run_api_benchmarks()}
        elif args.test_type == "load":
            results = {"load_testing": runner.run_load_tests()}
        elif args.test_type == "database":
            results = {"database_performance": runner.run_database_performance_tests()}
        elif args.test_type == "queue":
            results = {"queue_performance": runner.run_queue_performance_tests()}
        elif args.test_type == "resources":
            results = {"resource_monitoring": runner.run_resource_tests()}
        
        runner.generate_performance_report({
            "timestamp": runner.test_timestamp,
            "service_url": args.service_url,
            "system_info": runner.get_system_info(),
            "tests": results
        })
    
    print("\n🎉 Performance testing completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())