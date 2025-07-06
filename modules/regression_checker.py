import subprocess
import ast
import importlib.util
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CheckResult:
    """Result of code quality check"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    score: int  # 0-100 quality score

class RegressionChecker:
    def __init__(self):
        self.tools_available = self._check_available_tools()
        
    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which linting tools are available"""
        tools = {
            'pyflakes': self._tool_available('pyflakes'),
            'pylint': self._tool_available('pylint'),
            'black': self._tool_available('black'),
            'isort': self._tool_available('isort'),
            'bandit': self._tool_available('bandit'),
        }
        return tools
    
    def _tool_available(self, tool: str) -> bool:
        """Check if a tool is available"""
        try:
            subprocess.run([tool, '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def comprehensive_check(self, file_path: str) -> CheckResult:
        """Run comprehensive code quality checks"""
        result = CheckResult(
            passed=True,
            errors=[],
            warnings=[],
            suggestions=[],
            score=100
        )
        
        # 1. Syntax validation
        syntax_ok = self._check_syntax(file_path, result)
        
        # 2. Static analysis
        if syntax_ok:
            self._run_static_analysis(file_path, result)
            
        # 3. Security scan
        self._security_scan(file_path, result)
        
        # 4. Import validation
        self._check_imports(file_path, result)
        
        # 5. Pyrogram-specific checks
        self._pyrogram_checks(file_path, result)
        
        # 6. Calculate final score
        result.score = self._calculate_score(result)
        result.passed = result.score >= 70 and len(result.errors) == 0
        
        return result
    
    def _check_syntax(self, file_path: str, result: CheckResult) -> bool:
        """Check Python syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast.parse(content)
            
            # Also run pyflakes if available
            if self.tools_available['pyflakes']:
                pyflakes_result = subprocess.run(
                    ['pyflakes', file_path],
                    capture_output=True, text=True
                )
                
                if pyflakes_result.returncode != 0:
                    errors = pyflakes_result.stdout + pyflakes_result.stderr
                    result.errors.extend(errors.strip().split('\n'))
                    
            return True
            
        except SyntaxError as e:
            result.errors.append(f"Syntax Error: {e}")
            return False
        except Exception as e:
            result.errors.append(f"File Error: {e}")
            return False
    
    def _run_static_analysis(self, file_path: str, result: CheckResult):
        """Run static analysis tools"""
        
        # Pylint check
        if self.tools_available['pylint']:
            try:
                pylint_result = subprocess.run(
                    ['pylint', file_path, '--output-format=text', '--score=no'],
                    capture_output=True, text=True
                )
                
                if pylint_result.stdout:
                    lines = pylint_result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('E:'):
                            result.errors.append(f"Pylint Error: {line}")
                        elif line.startswith('W:'):
                            result.warnings.append(f"Pylint Warning: {line}")
                        elif line.startswith('C:') or line.startswith('R:'):
                            result.suggestions.append(f"Pylint: {line}")
                            
            except Exception as e:
                logger.warning(f"Pylint check failed: {e}")
    
    def _security_scan(self, file_path: str, result: CheckResult):
        """Run security scans"""
        if self.tools_available['bandit']:
            try:
                bandit_result = subprocess.run(
                    ['bandit', '-f', 'txt', file_path],
                    capture_output=True, text=True
                )
                
                if bandit_result.returncode != 0:
                    # Parse bandit output for security issues
                    if 'High:' in bandit_result.stdout:
                        result.errors.append("Security: High severity issues found")
                    elif 'Medium:' in bandit_result.stdout:
                        result.warnings.append("Security: Medium severity issues found")
                    elif 'Low:' in bandit_result.stdout:
                        result.suggestions.append("Security: Low severity issues found")
                        
            except Exception as e:
                logger.warning(f"Security scan failed: {e}")
    
    def _check_imports(self, file_path: str, result: CheckResult):
        """Validate imports and dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for required Pyrogram imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Validate critical imports exist
            required_imports = ['pyrogram']
            missing_imports = [imp for imp in required_imports 
                             if not any(imp in existing for existing in imports)]
            
            if missing_imports:
                result.warnings.append(f"Missing imports: {', '.join(missing_imports)}")
                
        except Exception as e:
            result.warnings.append(f"Import check failed: {e}")
    
    def _pyrogram_checks(self, file_path: str, result: CheckResult):
        """Pyrogram-specific validation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for register_handlers function
            if 'register_handlers' not in content:
                result.errors.append("Missing register_handlers function")
            
            # Check for proper async/await usage
            if '@bot.on_message' in content and 'async def' not in content:
                result.errors.append("Message handlers must be async")
            
            # Check for proper error handling
            if 'try:' not in content and '@bot.on_message' in content:
                result.suggestions.append("Consider adding error handling")
                
        except Exception as e:
            result.warnings.append(f"Pyrogram check failed: {e}")
    
    def _calculate_score(self, result: CheckResult) -> int:
        """Calculate quality score"""
        score = 100
        
        # Deduct points for issues
        score -= len(result.errors) * 20
        score -= len(result.warnings) * 10
        score -= len(result.suggestions) * 5
        
        return max(0, score)
    
    def auto_fix(self, file_path: str) -> bool:
        """Attempt to auto-fix common issues"""
        try:
            fixed = False
            
            # Auto-format with black
            if self.tools_available['black']:
                subprocess.run(['black', file_path], check=True)
                fixed = True
            
            # Sort imports with isort
            if self.tools_available['isort']:
                subprocess.run(['isort', file_path], check=True)
                fixed = True
            
            return fixed
            
        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            return False
    
    def get_fix_suggestions(self, file_path: str) -> List[str]:
        """Get actionable fix suggestions"""
        result = self.comprehensive_check(file_path)
        
        suggestions = []
        
        if result.errors:
            suggestions.append("🔴 Critical errors found - code will not work")
        
        if result.warnings:
            suggestions.append("🟡 Warnings found - code may have issues")
        
        if result.score < 70:
            suggestions.append("📊 Code quality below threshold")
        
        if not self.tools_available['pylint']:
            suggestions.append("💡 Install pylint for better analysis")
        
        return suggestions

# Legacy function for backward compatibility
def lint_code(file_path: str) -> str:
    """Legacy function - use comprehensive_check instead"""
    checker = EnhancedRegressionChecker()
    result = checker.comprehensive_check(file_path)
    
    output = []
    if result.errors:
        output.extend([f"ERROR: {e}" for e in result.errors])
    if result.warnings:
        output.extend([f"WARNING: {w}" for w in result.warnings])
    if result.suggestions:
        output.extend([f"SUGGESTION: {s}" for s in result.suggestions])
    
    output.append(f"QUALITY SCORE: {result.score}/100")
    output.append(f"PASSED: {'✅' if result.passed else '❌'}")
    
    return '\n'.join(output)

# Global instance
regression_checker = EnhancedRegressionChecker()
