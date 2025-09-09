#!/usr/bin/env python3
"""
Code Quality and Standards Checker for Auth Service
Ensures code follows best practices and style guidelines
"""

import os
import sys
import ast
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

@dataclass
class QualityIssue:
    """Code quality issue"""
    type: str
    severity: str
    file_path: str
    line_number: Optional[int]
    message: str
    suggestion: Optional[str] = None

class CodeQualityChecker:
    """Main code quality checker"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.issues: List[QualityIssue] = []
        
        # Coding standards
        self.max_line_length = 88  # Black default
        self.max_function_length = 50
        self.max_class_length = 200
        self.max_complexity = 10
        
        # Required docstring patterns
        self.docstring_patterns = {
            "function": r'""".*?"""',
            "class": r'""".*?"""',
            "module": r'""".*?"""'
        }

    def run_quality_checks(self) -> bool:
        """Run all code quality checks"""
        print("🔍 Running code quality checks...")
        
        self.issues = []
        
        # Core checks
        self.check_code_style()
        self.check_docstrings()
        self.check_complexity()
        self.check_security_patterns()
        self.check_performance_patterns()
        self.check_error_handling()
        
        # External tool checks
        self.run_external_tools()
        
        # Report results
        self.report_quality_results()
        
        return len([i for i in self.issues if i.severity == 'error']) == 0

    def check_code_style(self):
        """Check code style and formatting"""
        print("  📝 Checking code style...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    # Check line length
                    if len(line.rstrip()) > self.max_line_length:
                        self.issues.append(QualityIssue(
                            type="style",
                            severity="warning",
                            file_path=str(file_path),
                            line_number=line_num,
                            message=f"Line too long ({len(line.rstrip())} > {self.max_line_length})",
                            suggestion="Break line or use Black formatter"
                        ))
                    
                    # Check trailing whitespace
                    if line.endswith(' \n') or line.endswith('\t\n'):
                        self.issues.append(QualityIssue(
                            type="style",
                            severity="info",
                            file_path=str(file_path),
                            line_number=line_num,
                            message="Trailing whitespace",
                            suggestion="Remove trailing whitespace"
                        ))
                    
                    # Check TODO comments
                    if 'TODO' in line.upper() or 'FIXME' in line.upper():
                        self.issues.append(QualityIssue(
                            type="maintenance",
                            severity="info",
                            file_path=str(file_path),
                            line_number=line_num,
                            message="TODO/FIXME comment found",
                            suggestion="Address or document the TODO item"
                        ))
                
            except Exception as e:
                continue

    def check_docstrings(self):
        """Check for missing or inadequate docstrings"""
        print("  📚 Checking docstrings...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            if file_path.name == "__init__.py":
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check module docstring
                if not ast.get_docstring(tree):
                    self.issues.append(QualityIssue(
                        type="documentation",
                        severity="warning",
                        file_path=str(file_path),
                        line_number=1,
                        message="Missing module docstring",
                        suggestion="Add module-level docstring explaining the file's purpose"
                    ))
                
                # Check class and function docstrings
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private methods and test methods
                        if node.name.startswith('_') or node.name.startswith('test_'):
                            continue
                            
                        if not ast.get_docstring(node):
                            self.issues.append(QualityIssue(
                                type="documentation",
                                severity="warning",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                message=f"Missing docstring for function '{node.name}'",
                                suggestion="Add docstring explaining function purpose, parameters, and return value"
                            ))
                    
                    elif isinstance(node, ast.ClassDef):
                        if not ast.get_docstring(node):
                            self.issues.append(QualityIssue(
                                type="documentation",
                                severity="warning",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                message=f"Missing docstring for class '{node.name}'",
                                suggestion="Add docstring explaining class purpose and usage"
                            ))
                
            except Exception as e:
                continue

    def check_complexity(self):
        """Check code complexity metrics"""
        print("  🧮 Checking code complexity...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate cyclomatic complexity (simplified)
                        complexity = self.calculate_complexity(node)
                        
                        if complexity > self.max_complexity:
                            self.issues.append(QualityIssue(
                                type="complexity",
                                severity="warning",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                message=f"Function '{node.name}' too complex (complexity: {complexity})",
                                suggestion="Break into smaller functions or reduce branching"
                            ))
                        
                        # Check function length
                        func_length = self.get_node_length(node)
                        if func_length > self.max_function_length:
                            self.issues.append(QualityIssue(
                                type="complexity",
                                severity="info",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                message=f"Function '{node.name}' too long ({func_length} lines)",
                                suggestion="Consider breaking into smaller functions"
                            ))
                    
                    elif isinstance(node, ast.ClassDef):
                        # Check class length
                        class_length = self.get_node_length(node)
                        if class_length > self.max_class_length:
                            self.issues.append(QualityIssue(
                                type="complexity",
                                severity="info",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                message=f"Class '{node.name}' too long ({class_length} lines)",
                                suggestion="Consider breaking into smaller classes or using composition"
                            ))
                
            except Exception as e:
                continue

    def check_security_patterns(self):
        """Check for common security issues"""
        print("  🔒 Checking security patterns...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']*["\']', "Hardcoded password detected"),
            (r'secret\s*=\s*["\'][^"\']*["\']', "Hardcoded secret detected"),
            (r'api_key\s*=\s*["\'][^"\']*["\']', "Hardcoded API key detected"),
            (r'exec\s*\(', "Use of exec() function detected"),
            (r'eval\s*\(', "Use of eval() function detected"),
            (r'shell\s*=\s*True', "Shell injection risk detected"),
            (r'pickle\.loads?\(', "Unsafe pickle usage detected"),
        ]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, message in security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.issues.append(QualityIssue(
                                type="security",
                                severity="error",
                                file_path=str(file_path),
                                line_number=line_num,
                                message=message,
                                suggestion="Use environment variables or secure configuration"
                            ))
                
            except Exception as e:
                continue

    def check_performance_patterns(self):
        """Check for performance anti-patterns"""
        print("  ⚡ Checking performance patterns...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    # Check for string concatenation in loops
                    if isinstance(node, (ast.For, ast.While)):
                        for child in ast.walk(node):
                            if (isinstance(child, ast.AugAssign) and 
                                isinstance(child.op, ast.Add) and
                                isinstance(child.target, ast.Name)):
                                # Potential string concatenation in loop
                                self.issues.append(QualityIssue(
                                    type="performance",
                                    severity="info",
                                    file_path=str(file_path),
                                    line_number=node.lineno,
                                    message="Potential inefficient string concatenation in loop",
                                    suggestion="Use list.join() or f-strings for better performance"
                                ))
                    
                    # Check for bare except clauses
                    if isinstance(node, ast.ExceptHandler) and not node.type:
                        self.issues.append(QualityIssue(
                            type="error_handling",
                            severity="warning",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            message="Bare except clause detected",
                            suggestion="Catch specific exception types"
                        ))
                
            except Exception as e:
                continue

    def check_error_handling(self):
        """Check error handling patterns"""
        print("  🚨 Checking error handling...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    # Check for empty except blocks
                    if (isinstance(node, ast.ExceptHandler) and 
                        len(node.body) == 1 and
                        isinstance(node.body[0], ast.Pass)):
                        self.issues.append(QualityIssue(
                            type="error_handling",
                            severity="warning",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            message="Empty except block detected",
                            suggestion="Add proper error handling or logging"
                        ))
                    
                    # Check for print statements (should use logging)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id == 'print':
                            self.issues.append(QualityIssue(
                                type="logging",
                                severity="info",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                message="Use logging instead of print statements",
                                suggestion="Replace with appropriate logging level"
                            ))
                
            except Exception as e:
                continue

    def run_external_tools(self):
        """Run external code quality tools"""
        print("  🔧 Running external tools...")
        
        tools = [
            ("flake8", ["flake8", "--max-line-length=88", "--extend-ignore=E203,W503"]),
            ("mypy", ["mypy", "--ignore-missing-imports"]),
            ("bandit", ["bandit", "-r", ".", "-f", "json"]),
        ]
        
        for tool_name, cmd in tools:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.root_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0 and result.stdout:
                    # Parse tool output (simplified)
                    self.issues.append(QualityIssue(
                        type="external_tool",
                        severity="info",
                        file_path="multiple",
                        line_number=None,
                        message=f"{tool_name} found issues",
                        suggestion=f"Run '{' '.join(cmd)}' for details"
                    ))
                        
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Tool not available or timed out
                continue

    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity

    def get_node_length(self, node: ast.AST) -> int:
        """Get the length of an AST node in lines"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 0

    def report_quality_results(self):
        """Report code quality results"""
        errors = [i for i in self.issues if i.severity == 'error']
        warnings = [i for i in self.issues if i.severity == 'warning']
        info = [i for i in self.issues if i.severity == 'info']
        
        print(f"\n📊 Code Quality Results:")
        print(f"❌ Errors: {len(errors)}")
        print(f"⚠️  Warnings: {len(warnings)}")
        print(f"ℹ️  Info: {len(info)}")
        
        # Show critical issues
        for error in errors[:5]:
            print(f"  ❌ {error.message}")
            print(f"     {error.file_path}:{error.line_number}")
            if error.suggestion:
                print(f"     💡 {error.suggestion}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Quality Checker")
    parser.add_argument("--path", default=".", help="Root path to check")
    
    args = parser.parse_args()
    
    checker = CodeQualityChecker(args.path)
    success = checker.run_quality_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()