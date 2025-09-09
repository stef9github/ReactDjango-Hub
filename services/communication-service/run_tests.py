#!/usr/bin/env python3
"""
Comprehensive test runner and validation script
Validates test coverage, quality metrics, and generates reports
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import argparse


class TestRunner:
    """Comprehensive test runner with validation and reporting"""
    
    def __init__(self):
        self.test_root = Path(__file__).parent / "tests"
        self.coverage_threshold = 80
        self.auth_coverage_threshold = 100
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "test_results": {},
            "coverage_results": {},
            "quality_metrics": {},
            "recommendations": []
        }
    
    def run_command(self, command, capture_output=True):
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                check=False
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def install_test_dependencies(self):
        """Install test dependencies"""
        print("📦 Installing test dependencies...")
        
        # Check if test_requirements.txt exists
        test_req_file = Path("test_requirements.txt")
        if not test_req_file.exists():
            print("❌ test_requirements.txt not found")
            return False
        
        # Install test dependencies
        result = self.run_command("pip install -r test_requirements.txt")
        if not result["success"]:
            print(f"❌ Failed to install test dependencies: {result['stderr']}")
            return False
        
        print("✅ Test dependencies installed successfully")
        return True
    
    def validate_test_structure(self):
        """Validate test directory structure"""
        print("🏗️ Validating test structure...")
        
        required_dirs = [
            "tests/unit",
            "tests/integration", 
            "tests/e2e",
            "tests/fixtures"
        ]
        
        required_files = [
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
            "tests/e2e/__init__.py",
            "tests/fixtures/__init__.py",
            "pytest.ini"
        ]
        
        missing_dirs = []
        missing_files = []
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_dirs:
            print(f"❌ Missing directories: {', '.join(missing_dirs)}")
            return False
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        
        print("✅ Test structure validation passed")
        return True
    
    def run_unit_tests(self):
        """Run unit tests with coverage"""
        print("🧪 Running unit tests...")
        
        command = "pytest tests/unit -v --cov=. --cov-report=term-missing --cov-report=json:coverage-unit.json -m unit"
        result = self.run_command(command)
        
        self.results["test_results"]["unit"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            print("✅ Unit tests passed")
            return True
        else:
            print(f"❌ Unit tests failed: {result['stderr']}")
            return False
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("🔗 Running integration tests...")
        
        command = "pytest tests/integration -v --cov=. --cov-report=json:coverage-integration.json -m integration"
        result = self.run_command(command)
        
        self.results["test_results"]["integration"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            print("✅ Integration tests passed")
            return True
        else:
            print(f"❌ Integration tests failed: {result['stderr']}")
            return False
    
    def run_auth_tests(self):
        """Run authentication tests specifically"""
        print("🔐 Running authentication tests...")
        
        command = "pytest tests/integration/test_auth_integration.py -v --cov=. --cov-report=json:coverage-auth.json -m auth"
        result = self.run_command(command)
        
        self.results["test_results"]["auth"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            print("✅ Authentication tests passed")
            return True
        else:
            print(f"❌ Authentication tests failed: {result['stderr']}")
            return False
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        print("🌐 Running end-to-end tests...")
        
        command = "pytest tests/e2e -v -m e2e --tb=short"
        result = self.run_command(command)
        
        self.results["test_results"]["e2e"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            print("✅ End-to-end tests passed")
            return True
        else:
            print(f"❌ End-to-end tests failed: {result['stderr']}")
            return False
    
    def run_all_tests_with_coverage(self):
        """Run all tests with comprehensive coverage"""
        print("📊 Running all tests with coverage...")
        
        command = "pytest --cov=. --cov-report=html:htmlcov --cov-report=json:coverage.json --cov-report=term-missing --cov-fail-under=80"
        result = self.run_command(command)
        
        self.results["test_results"]["comprehensive"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        return result["success"]
    
    def analyze_coverage(self):
        """Analyze test coverage results"""
        print("📈 Analyzing test coverage...")
        
        coverage_files = [
            "coverage.json",
            "coverage-unit.json",
            "coverage-integration.json",
            "coverage-auth.json"
        ]
        
        coverage_data = {}
        
        for coverage_file in coverage_files:
            if Path(coverage_file).exists():
                try:
                    with open(coverage_file, 'r') as f:
                        data = json.load(f)
                        coverage_data[coverage_file] = data
                except Exception as e:
                    print(f"⚠️ Failed to read {coverage_file}: {e}")
        
        # Analyze overall coverage
        if "coverage.json" in coverage_data:
            overall_coverage = coverage_data["coverage.json"]
            total_coverage = overall_coverage.get("totals", {}).get("percent_covered", 0)
            
            self.results["coverage_results"]["overall"] = {
                "percentage": total_coverage,
                "meets_threshold": total_coverage >= self.coverage_threshold,
                "threshold": self.coverage_threshold
            }
            
            print(f"📊 Overall coverage: {total_coverage:.1f}%")
            
            if total_coverage >= self.coverage_threshold:
                print(f"✅ Coverage meets minimum threshold ({self.coverage_threshold}%)")
            else:
                print(f"❌ Coverage below threshold ({self.coverage_threshold}%)")
                self.results["recommendations"].append(
                    f"Increase test coverage from {total_coverage:.1f}% to at least {self.coverage_threshold}%"
                )
        
        # Analyze file-by-file coverage
        if "coverage.json" in coverage_data:
            files_data = coverage_data["coverage.json"].get("files", {})
            low_coverage_files = []
            
            for file_path, file_data in files_data.items():
                file_coverage = file_data.get("summary", {}).get("percent_covered", 0)
                if file_coverage < 70:  # Files with less than 70% coverage
                    low_coverage_files.append((file_path, file_coverage))
            
            if low_coverage_files:
                print("⚠️ Files with low coverage:")
                for file_path, coverage in low_coverage_files[:10]:  # Show top 10
                    print(f"   {file_path}: {coverage:.1f}%")
                
                self.results["recommendations"].append(
                    f"Improve coverage for {len(low_coverage_files)} files with low coverage"
                )
        
        return True
    
    def check_code_quality(self):
        """Check code quality metrics"""
        print("🔍 Checking code quality...")
        
        # Check if flake8 is available
        flake8_result = self.run_command("flake8 --version")
        if flake8_result["success"]:
            print("  Running flake8 linting...")
            lint_result = self.run_command("flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics")
            
            self.results["quality_metrics"]["linting"] = {
                "tool": "flake8",
                "success": lint_result["success"],
                "output": lint_result["stdout"]
            }
            
            if lint_result["success"]:
                print("  ✅ Linting passed")
            else:
                print(f"  ⚠️ Linting issues found: {lint_result['stdout']}")
        else:
            print("  ⚠️ flake8 not available, skipping linting")
        
        # Check if black is available for formatting
        black_result = self.run_command("black --version")
        if black_result["success"]:
            print("  Checking code formatting...")
            format_result = self.run_command("black --check --diff .")
            
            self.results["quality_metrics"]["formatting"] = {
                "tool": "black",
                "success": format_result["success"],
                "output": format_result["stdout"]
            }
            
            if format_result["success"]:
                print("  ✅ Code formatting is consistent")
            else:
                print("  ⚠️ Code formatting issues found")
                self.results["recommendations"].append("Run 'black .' to fix formatting issues")
        else:
            print("  ⚠️ black not available, skipping format check")
        
        return True
    
    def validate_auth_coverage(self):
        """Validate that authentication tests have 100% coverage"""
        print("🔐 Validating authentication test coverage...")
        
        # Run auth tests specifically with coverage
        auth_files = [
            "auth.py",
            "auth_middleware.py", 
            "identity_client.py",
            "jwt_handler.py"
        ]
        
        if Path("coverage.json").exists():
            try:
                with open("coverage.json", 'r') as f:
                    coverage_data = json.load(f)
                
                auth_coverage_issues = []
                files_data = coverage_data.get("files", {})
                
                for file_path, file_data in files_data.items():
                    if any(auth_file in file_path for auth_file in auth_files):
                        file_coverage = file_data.get("summary", {}).get("percent_covered", 0)
                        if file_coverage < self.auth_coverage_threshold:
                            auth_coverage_issues.append((file_path, file_coverage))
                
                if auth_coverage_issues:
                    print("❌ Authentication files with insufficient coverage:")
                    for file_path, coverage in auth_coverage_issues:
                        print(f"   {file_path}: {coverage:.1f}% (requires {self.auth_coverage_threshold}%)")
                    
                    self.results["recommendations"].append(
                        "Authentication files must have 100% test coverage for security reasons"
                    )
                    return False
                else:
                    print("✅ Authentication test coverage validated")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Failed to validate auth coverage: {e}")
                return False
        else:
            print("⚠️ No coverage data available for auth validation")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("📋 Generating test report...")
        
        report_file = "test_report.json"
        
        # Calculate overall status
        test_results = self.results["test_results"]
        all_tests_passed = all(
            result.get("success", False) 
            for result in test_results.values()
        )
        
        coverage_passed = self.results.get("coverage_results", {}).get("overall", {}).get("meets_threshold", False)
        
        if all_tests_passed and coverage_passed:
            self.results["overall_status"] = "passed"
        elif all_tests_passed:
            self.results["overall_status"] = "passed_with_warnings"
        else:
            self.results["overall_status"] = "failed"
        
        # Save report
        try:
            with open(report_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"✅ Test report generated: {report_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to generate report: {e}")
            return False
    
    def print_summary(self):
        """Print test execution summary"""
        print("\n" + "="*60)
        print("📊 TEST EXECUTION SUMMARY")
        print("="*60)
        
        # Overall status
        status_emoji = {
            "passed": "✅",
            "passed_with_warnings": "⚠️", 
            "failed": "❌",
            "unknown": "❓"
        }
        
        overall_status = self.results["overall_status"]
        print(f"Overall Status: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
        
        # Test results
        test_results = self.results["test_results"]
        if test_results:
            print("\nTest Results:")
            for test_type, result in test_results.items():
                status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
                print(f"  {test_type.title()}: {status}")
        
        # Coverage results
        coverage_results = self.results.get("coverage_results", {})
        if "overall" in coverage_results:
            coverage_data = coverage_results["overall"]
            percentage = coverage_data.get("percentage", 0)
            threshold = coverage_data.get("threshold", 0)
            meets_threshold = coverage_data.get("meets_threshold", False)
            
            status = "✅" if meets_threshold else "❌"
            print(f"\nCoverage: {status} {percentage:.1f}% (threshold: {threshold}%)")
        
        # Recommendations
        recommendations = self.results.get("recommendations", [])
        if recommendations:
            print("\nRecommendations:")
            for i, recommendation in enumerate(recommendations, 1):
                print(f"  {i}. {recommendation}")
        
        print("="*60)
    
    def run_quick_tests(self):
        """Run essential tests quickly"""
        print("⚡ Running quick test suite...")
        
        success = True
        
        # Run unit tests
        if not self.run_unit_tests():
            success = False
        
        # Run auth tests
        if not self.run_auth_tests():
            success = False
        
        # Basic coverage check
        command = "pytest tests/unit tests/integration/test_auth_integration.py --cov=. --cov-report=json:coverage-quick.json"
        result = self.run_command(command)
        
        if result["success"]:
            self.analyze_coverage()
        
        return success
    
    def run_full_validation(self):
        """Run complete test validation suite"""
        print("🚀 Running full test validation suite...")
        
        steps = [
            ("Validate test structure", self.validate_test_structure),
            ("Install test dependencies", self.install_test_dependencies),
            ("Run unit tests", self.run_unit_tests),
            ("Run integration tests", self.run_integration_tests), 
            ("Run authentication tests", self.run_auth_tests),
            ("Run E2E tests", self.run_e2e_tests),
            ("Run comprehensive coverage", self.run_all_tests_with_coverage),
            ("Analyze coverage", self.analyze_coverage),
            ("Validate auth coverage", self.validate_auth_coverage),
            ("Check code quality", self.check_code_quality),
            ("Generate report", self.generate_test_report)
        ]
        
        overall_success = True
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            try:
                step_success = step_func()
                if not step_success:
                    overall_success = False
                    print(f"❌ {step_name} failed")
                else:
                    print(f"✅ {step_name} completed")
            except Exception as e:
                print(f"❌ {step_name} failed with error: {e}")
                overall_success = False
        
        self.results["overall_status"] = "passed" if overall_success else "failed"
        return overall_success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner and validator")
    parser.add_argument(
        "--mode", 
        choices=["quick", "full"],
        default="full",
        help="Test mode: quick (essential tests) or full (complete validation)"
    )
    parser.add_argument(
        "--coverage-threshold",
        type=int,
        default=80,
        help="Minimum coverage threshold percentage"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner()
    runner.coverage_threshold = args.coverage_threshold
    
    print("🧪 Communication Service Test Suite")
    print("="*50)
    print(f"Mode: {args.mode}")
    print(f"Coverage threshold: {args.coverage_threshold}%")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("="*50)
    
    # Run tests based on mode
    if args.mode == "quick":
        success = runner.run_quick_tests()
    else:
        success = runner.run_full_validation()
    
    # Print summary
    runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()