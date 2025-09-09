#!/usr/bin/env python3
"""
Auth Service Organization Maintenance Script
Ensures proper directory structure, imports, and code organization
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

@dataclass
class ValidationIssue:
    """Represents a validation issue found during checks"""
    type: str
    severity: str  # 'error', 'warning', 'info'
    file_path: str
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

class AuthServiceOrganizer:
    """Main class for maintaining auth service organization"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.issues: List[ValidationIssue] = []
        
        # Expected directory structure
        self.expected_structure = {
            "app": {
                "api": {
                    "v1": ["auth.py", "users.py", "organizations.py", "mfa.py"],
                    "__files__": ["__init__.py", "deps.py"]
                },
                "core": ["__init__.py", "config.py", "database.py", "security.py"],
                "models": ["__init__.py", "enhanced_models.py"],
                "schemas": ["__init__.py", "auth.py", "user.py", "organization.py", "mfa.py"],
                "services": ["__init__.py", "auth_service.py", "user_service.py", "mfa_service.py", "email_service.py"],
                "utils": ["__init__.py", "messaging.py"],
                "__files__": ["__init__.py", "main.py"]
            },
            "tests": ["__init__.py"],
            "scripts": ["__init__.py"],
            "__files__": ["main.py", "requirements.txt", "Dockerfile", "docker-compose.yml"]
        }
        
        # Import rules
        self.import_rules = {
            "app/api/v1/*.py": {
                "allowed_patterns": [
                    "from fastapi import *",
                    "from app.api.deps import *",
                    "from app.schemas.* import *",
                    "from app.services.* import *",
                    "from app.utils.* import *"
                ],
                "forbidden_patterns": [
                    "from app.models.* import *",  # Should use services instead
                    "from app.core.database import *"  # Should use deps
                ]
            },
            "app/services/*.py": {
                "allowed_patterns": [
                    "from app.models.* import *",
                    "from app.core.* import *",
                    "from app.utils.* import *"
                ],
                "forbidden_patterns": [
                    "from app.api.* import *",  # Services shouldn't import API
                    "from app.schemas.* import *"  # Services shouldn't depend on schemas
                ]
            },
            "app/schemas/*.py": {
                "allowed_patterns": [
                    "from pydantic import *",
                    "from typing import *",
                    "from datetime import *",
                    "from enum import *"
                ],
                "forbidden_patterns": [
                    "from app.* import *"  # Schemas should be independent
                ]
            }
        }

    def run_all_checks(self) -> bool:
        """Run all organization checks"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔧 Auth Service Organization Checker{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}")
        
        self.issues = []
        
        # Run checks
        self.check_directory_structure()
        self.check_import_organization()
        self.check_code_organization()
        self.check_file_naming()
        self.check_missing_init_files()
        self.check_circular_imports()
        
        # Report results
        self.report_results()
        
        return len([i for i in self.issues if i.severity == 'error']) == 0

    def check_directory_structure(self):
        """Validate directory structure matches expected layout"""
        print(f"{Colors.YELLOW}📁 Checking directory structure...{Colors.END}")
        
        def check_structure(expected: Dict, current_path: Path, base_name: str = ""):
            for name, content in expected.items():
                if name == "__files__":
                    # Check files in current directory
                    for file_name in content:
                        file_path = current_path / file_name
                        if not file_path.exists():
                            self.issues.append(ValidationIssue(
                                type="structure",
                                severity="error",
                                file_path=str(file_path),
                                message=f"Missing required file: {file_name}",
                                suggestion=f"Create file: touch {file_path}"
                            ))
                else:
                    # Check directory
                    dir_path = current_path / name
                    if not dir_path.exists():
                        self.issues.append(ValidationIssue(
                            type="structure",
                            severity="error",
                            file_path=str(dir_path),
                            message=f"Missing required directory: {name}",
                            suggestion=f"Create directory: mkdir -p {dir_path}"
                        ))
                        continue
                    
                    if isinstance(content, dict):
                        check_structure(content, dir_path, f"{base_name}/{name}")
                    elif isinstance(content, list):
                        # Check files in this directory
                        for file_name in content:
                            file_path = dir_path / file_name
                            if not file_path.exists():
                                self.issues.append(ValidationIssue(
                                    type="structure",
                                    severity="error",
                                    file_path=str(file_path),
                                    message=f"Missing required file: {file_name}",
                                    suggestion=f"Create file: touch {file_path}"
                                ))
        
        check_structure(self.expected_structure, self.root_path)

    def check_import_organization(self):
        """Check import statements follow organization rules"""
        print(f"{Colors.YELLOW}📦 Checking import organization...{Colors.END}")
        
        for pattern, rules in self.import_rules.items():
            files = list(self.root_path.glob(pattern))
            
            for file_path in files:
                if not file_path.name.endswith('.py'):
                    continue
                    
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            import_line = self.get_import_line(content, node.lineno)
                            
                            # Check forbidden patterns
                            for forbidden in rules.get("forbidden_patterns", []):
                                if self.matches_pattern(import_line, forbidden):
                                    self.issues.append(ValidationIssue(
                                        type="imports",
                                        severity="error",
                                        file_path=str(file_path),
                                        message=f"Forbidden import pattern: {import_line}",
                                        line_number=node.lineno,
                                        suggestion=f"Use dependency injection or refactor to follow layer separation"
                                    ))
                
                except Exception as e:
                    self.issues.append(ValidationIssue(
                        type="imports",
                        severity="warning",
                        file_path=str(file_path),
                        message=f"Could not parse file for import analysis: {e}"
                    ))

    def check_code_organization(self):
        """Check code organization within files"""
        print(f"{Colors.YELLOW}🏗️  Checking code organization...{Colors.END}")
        
        # Check API endpoints organization
        api_files = list((self.root_path / "app" / "api" / "v1").glob("*.py"))
        for file_path in api_files:
            if file_path.name == "__init__.py":
                continue
                
            self.check_api_file_organization(file_path)
        
        # Check service files organization
        service_files = list((self.root_path / "app" / "services").glob("*.py"))
        for file_path in service_files:
            if file_path.name == "__init__.py":
                continue
                
            self.check_service_file_organization(file_path)

    def check_api_file_organization(self, file_path: Path):
        """Check API file follows proper organization"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for router creation
            if 'router = APIRouter(' not in content:
                self.issues.append(ValidationIssue(
                    type="organization",
                    severity="error",
                    file_path=str(file_path),
                    message="API file missing router creation",
                    suggestion="Add: router = APIRouter(prefix='/prefix', tags=['Tags'])"
                ))
            
            # Check for proper endpoint decorators
            endpoint_pattern = r'@router\.(get|post|put|delete|patch)\('
            endpoints = re.findall(endpoint_pattern, content)
            
            if not endpoints:
                self.issues.append(ValidationIssue(
                    type="organization",
                    severity="warning",
                    file_path=str(file_path),
                    message="API file contains no endpoints"
                ))
                
        except Exception as e:
            self.issues.append(ValidationIssue(
                type="organization",
                severity="warning", 
                file_path=str(file_path),
                message=f"Could not analyze API file organization: {e}"
            ))

    def check_service_file_organization(self, file_path: Path):
        """Check service file follows proper organization"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for class definition
            class_pattern = r'class \w+Service\w*:'
            if not re.search(class_pattern, content):
                self.issues.append(ValidationIssue(
                    type="organization",
                    severity="warning",
                    file_path=str(file_path),
                    message="Service file should contain a Service class"
                ))
                
        except Exception as e:
            self.issues.append(ValidationIssue(
                type="organization", 
                severity="warning",
                file_path=str(file_path),
                message=f"Could not analyze service file organization: {e}"
            ))

    def check_file_naming(self):
        """Check file naming conventions"""
        print(f"{Colors.YELLOW}📝 Checking file naming conventions...{Colors.END}")
        
        # Check Python files follow snake_case
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            name = file_path.stem
            
            # Skip special files
            if name in ["__init__", "__main__"]:
                continue
            
            # Check snake_case
            if not re.match(r'^[a-z][a-z0-9_]*$', name):
                self.issues.append(ValidationIssue(
                    type="naming",
                    severity="warning",
                    file_path=str(file_path),
                    message=f"File name should follow snake_case convention: {name}",
                    suggestion=f"Rename to use snake_case"
                ))

    def check_missing_init_files(self):
        """Check for missing __init__.py files"""
        print(f"{Colors.YELLOW}🔍 Checking for missing __init__.py files...{Colors.END}")
        
        # Find all directories that should have __init__.py
        python_dirs = set()
        for py_file in self.root_path.rglob("*.py"):
            python_dirs.add(py_file.parent)
        
        for directory in python_dirs:
            # Skip root directory and non-package directories
            if directory == self.root_path:
                continue
            
            init_file = directory / "__init__.py"
            if not init_file.exists():
                self.issues.append(ValidationIssue(
                    type="structure",
                    severity="warning",
                    file_path=str(init_file),
                    message=f"Missing __init__.py in Python package directory",
                    suggestion=f"Create file: touch {init_file}"
                ))

    def check_circular_imports(self):
        """Check for potential circular imports"""
        print(f"{Colors.YELLOW}🔄 Checking for circular imports...{Colors.END}")
        
        import_graph = defaultdict(set)
        
        # Build import graph
        for py_file in self.root_path.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_module = self.get_module_name(py_file)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('app.'):
                            import_graph[file_module].add(node.module)
                            
            except Exception:
                continue
        
        # Simple cycle detection (basic implementation)
        visited = set()
        rec_stack = set()
        
        def has_cycle(module):
            if module in rec_stack:
                return True
            if module in visited:
                return False
            
            visited.add(module)
            rec_stack.add(module)
            
            for neighbor in import_graph.get(module, set()):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(module)
            return False
        
        for module in import_graph:
            if module not in visited:
                if has_cycle(module):
                    self.issues.append(ValidationIssue(
                        type="imports",
                        severity="error",
                        file_path=module,
                        message="Potential circular import detected",
                        suggestion="Refactor to remove circular dependencies"
                    ))

    def auto_fix_issues(self):
        """Automatically fix issues that can be safely fixed"""
        print(f"{Colors.BOLD}{Colors.GREEN}🔧 Auto-fixing issues...{Colors.END}")
        
        fixed_count = 0
        
        for issue in self.issues:
            if issue.type == "structure" and "Missing" in issue.message:
                if "directory" in issue.message:
                    # Create missing directory
                    os.makedirs(issue.file_path, exist_ok=True)
                    print(f"  ✅ Created directory: {issue.file_path}")
                    fixed_count += 1
                elif issue.file_path.endswith("__init__.py"):
                    # Create missing __init__.py
                    Path(issue.file_path).touch()
                    print(f"  ✅ Created file: {issue.file_path}")
                    fixed_count += 1
        
        if fixed_count > 0:
            print(f"{Colors.GREEN}✨ Auto-fixed {fixed_count} issues{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️  No auto-fixable issues found{Colors.END}")

    def generate_organization_report(self):
        """Generate detailed organization report"""
        report_path = self.root_path / "ORGANIZATION_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Auth Service Organization Report\n\n")
            f.write(f"Generated on: {os.popen('date').read().strip()}\n\n")
            
            # Structure overview
            f.write("## Directory Structure\n\n")
            f.write("```\n")
            f.write(self.generate_tree_view())
            f.write("```\n\n")
            
            # Issues summary
            f.write("## Issues Found\n\n")
            
            issue_types = defaultdict(list)
            for issue in self.issues:
                issue_types[issue.type].append(issue)
            
            for issue_type, issues in issue_types.items():
                f.write(f"### {issue_type.title()} Issues ({len(issues)})\n\n")
                
                for issue in issues:
                    f.write(f"- **{issue.severity.upper()}**: {issue.message}\n")
                    f.write(f"  - File: `{issue.file_path}`\n")
                    if issue.line_number:
                        f.write(f"  - Line: {issue.line_number}\n")
                    if issue.suggestion:
                        f.write(f"  - Suggestion: {issue.suggestion}\n")
                    f.write("\n")
            
            # Best practices
            f.write("## Organization Best Practices\n\n")
            f.write("### API Layer (`app/api/`)\n")
            f.write("- Keep route handlers thin\n")
            f.write("- Use dependency injection for services\n")
            f.write("- Group related endpoints in same file\n\n")
            
            f.write("### Services Layer (`app/services/`)\n")
            f.write("- Contain all business logic\n")
            f.write("- No direct database access in API routes\n")
            f.write("- Use dependency injection for database sessions\n\n")
            
            f.write("### Models (`app/models/`)\n")
            f.write("- Only SQLAlchemy models\n")
            f.write("- No business logic in models\n\n")
            
            f.write("### Schemas (`app/schemas/`)\n")
            f.write("- Pydantic models for validation\n")
            f.write("- Separate request/response schemas\n")
            f.write("- No dependencies on other app modules\n\n")
        
        print(f"{Colors.GREEN}📄 Organization report generated: {report_path}{Colors.END}")

    # Helper methods
    def get_import_line(self, content: str, line_number: int) -> str:
        """Get the import line from content"""
        lines = content.split('\n')
        if line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""

    def matches_pattern(self, import_line: str, pattern: str) -> bool:
        """Check if import line matches forbidden pattern"""
        # Simple pattern matching - can be enhanced
        pattern_regex = pattern.replace('*', '.*')
        return re.match(pattern_regex, import_line) is not None

    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        try:
            rel_path = file_path.relative_to(self.root_path)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]  # Remove .py extension
            if parts[-1] == '__init__':
                parts.pop()  # Remove __init__
            return '.'.join(parts)
        except ValueError:
            return str(file_path)

    def generate_tree_view(self) -> str:
        """Generate tree view of directory structure"""
        def tree_recursive(directory: Path, prefix: str = "") -> List[str]:
            lines = []
            try:
                entries = sorted([p for p in directory.iterdir() if not p.name.startswith('.')])
                dirs = [p for p in entries if p.is_dir()]
                files = [p for p in entries if p.is_file()]
                
                for i, d in enumerate(dirs):
                    is_last_dir = (i == len(dirs) - 1 and len(files) == 0)
                    lines.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{d.name}/")
                    extension = "    " if is_last_dir else "│   "
                    lines.extend(tree_recursive(d, prefix + extension))
                
                for i, f in enumerate(files):
                    is_last = (i == len(files) - 1)
                    lines.append(f"{prefix}{'└── ' if is_last else '├── '}{f.name}")
                    
            except PermissionError:
                pass
                
            return lines
        
        lines = [f"{self.root_path.name}/"]
        lines.extend(tree_recursive(self.root_path))
        return '\n'.join(lines)

    def report_results(self):
        """Report validation results"""
        errors = [i for i in self.issues if i.severity == 'error']
        warnings = [i for i in self.issues if i.severity == 'warning']
        
        print(f"\n{Colors.CYAN}{'='*50}{Colors.END}")
        print(f"{Colors.BOLD}📊 Organization Check Results{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}")
        
        if not self.issues:
            print(f"{Colors.GREEN}✅ All checks passed! Organization is perfect.{Colors.END}")
            return
        
        print(f"{Colors.RED}❌ Errors: {len(errors)}{Colors.END}")
        print(f"{Colors.YELLOW}⚠️  Warnings: {len(warnings)}{Colors.END}")
        
        # Show errors
        if errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS:{Colors.END}")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  {Colors.RED}✗{Colors.END} {error.message}")
                print(f"    📁 {error.file_path}")
                if error.suggestion:
                    print(f"    💡 {error.suggestion}")
                print()
        
        # Show warnings
        if warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}WARNINGS:{Colors.END}")
            for warning in warnings[:5]:  # Show first 5 warnings
                print(f"  {Colors.YELLOW}⚠{Colors.END} {warning.message}")
                print(f"    📁 {warning.file_path}")
                if warning.suggestion:
                    print(f"    💡 {warning.suggestion}")
                print()
        
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more warnings")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auth Service Organization Maintenance")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--path", default=".", help="Root path to check (default: current directory)")
    
    args = parser.parse_args()
    
    organizer = AuthServiceOrganizer(args.path)
    
    # Run checks
    success = organizer.run_all_checks()
    
    # Auto-fix if requested
    if args.fix:
        organizer.auto_fix_issues()
        # Re-run checks after fixing
        print(f"\n{Colors.BLUE}🔄 Re-running checks after auto-fix...{Colors.END}")
        success = organizer.run_all_checks()
    
    # Generate report if requested
    if args.report:
        organizer.generate_organization_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()