import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import time

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    execution_time: float
    exit_code: int

class VenvExecutionEngine:
    def __init__(self, base_venv_path: Optional[str] = None):
        self.base_venv_path = base_venv_path or os.path.join(os.getcwd(), "venv")
        self.temp_dir = None
        
    def create_temp_script(self, code: str) -> str:
        """创建临时Python脚本文件"""
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp()
        
        script_path = os.path.join(self.temp_dir, f"script_{int(time.time())}.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return script_path
    
    def install_packages(self, packages: List[str]) -> bool:
        """在虚拟环境中安装包"""
        if not packages:
            return True
            
        try:
            # 获取虚拟环境的pip路径
            if sys.platform == "win32":
                pip_path = os.path.join(self.base_venv_path, "Scripts", "pip")
            else:
                pip_path = os.path.join(self.base_venv_path, "bin", "pip")
            
            for package in packages:
                result = subprocess.run(
                    [pip_path, "install", package],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode != 0:
                    print(f"安装包 {package} 失败: {result.stderr}")
                    return False
                else:
                    print(f"成功安装包: {package}")
            
            return True
            
        except subprocess.TimeoutExpired:
            print("包安装超时")
            return False
        except Exception as e:
            print(f"安装包时出错: {str(e)}")
            return False
    
    def execute_code(self, code: str, install_deps: bool = True) -> ExecutionResult:
        """在虚拟环境中执行Python代码"""
        start_time = time.time()
        
        try:
            # 创建临时脚本
            script_path = self.create_temp_script(code)
            
            # 如果需要，自动检测和安装依赖
            if install_deps:
                dependencies = self._extract_imports(code)
                if dependencies:
                    print(f"检测到依赖: {dependencies}")
                    if not self.install_packages(dependencies):
                        return ExecutionResult(
                            success=False,
                            output="",
                            error="依赖安装失败",
                            execution_time=time.time() - start_time,
                            exit_code=-1
                        )
            
            # 获取虚拟环境的Python解释器路径
            if sys.platform == "win32":
                python_path = os.path.join(self.base_venv_path, "Scripts", "python")
            else:
                python_path = os.path.join(self.base_venv_path, "bin", "python")
            
            # 执行代码
            result = subprocess.run(
                [python_path, script_path],
                capture_output=True,
                text=True,
                timeout=60,  # 1分钟超时
                cwd=os.path.dirname(script_path)
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                execution_time=execution_time,
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error="代码执行超时",
                execution_time=time.time() - start_time,
                exit_code=-1
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"执行出错: {str(e)}",
                execution_time=time.time() - start_time,
                exit_code=-1
            )
        finally:
            # 清理临时文件
            self._cleanup()
    
    def execute_with_retry(self, code: str, generator, original_request: str, max_retries: int = 2) -> tuple[ExecutionResult, str, int]:
        """
        执行代码，如果失败则自动重试修复
        
        Args:
            code: 要执行的代码
            generator: 代码生成器实例
            original_request: 原始用户请求
            max_retries: 最大重试次数
            
        Returns:
            tuple: (执行结果, 最终代码, 尝试次数)
        """
        current_code = code
        
        for attempt in range(max_retries + 1):
            result = self.execute_code(current_code)
            
            if result.success:
                return result, current_code, attempt + 1
            
            # 如果执行失败且还有重试机会
            if attempt < max_retries:
                try:
                    print(f"代码执行失败，尝试修复... (第{attempt + 1}次)")
                    
                    # 使用AI修复代码
                    fixed_code = generator.fix_code_with_error(
                        original_request, 
                        current_code, 
                        result.error, 
                        attempt + 1
                    )
                    
                    current_code = fixed_code.code
                    print(f"修复后的代码已生成，准备重新执行...")
                    
                except Exception as e:
                    print(f"代码修复失败: {str(e)}")
                    break
            else:
                print(f"已达到最大重试次数({max_retries})，停止修复")
        
        return result, current_code, max_retries + 1
    
    def _extract_imports(self, code: str) -> List[str]:
        """从代码中提取需要安装的第三方包"""
        import re
        
        # 匹配import语句
        import_pattern = r'^(?:from\s+([a-zA-Z_][a-zA-Z0-9_]*)|import\s+([a-zA-Z_][a-zA-Z0-9_]*)).*$'
        imports = re.findall(import_pattern, code, re.MULTILINE)
        
        packages = set()
        for from_import, direct_import in imports:
            package = from_import or direct_import
            if package and not self._is_stdlib(package):
                packages.add(package)
        
        return list(packages)
    
    def _is_stdlib(self, package: str) -> bool:
        """检查是否为Python标准库"""
        stdlib_packages = {
            'os', 'sys', 'json', 'datetime', 'time', 'random', 'math', 'collections',
            'itertools', 'functools', 'pathlib', 're', 'urllib', 'http', 'socket',
            'threading', 'multiprocessing', 'subprocess', 'csv', 'sqlite3', 'logging',
            'unittest', 'pickle', 'base64', 'hashlib', 'uuid', 'tempfile', 'shutil',
            'glob', 'platform', 'warnings', 'traceback', 'inspect', 'typing', 'abc',
            'argparse', 'calendar', 'configparser', 'contextlib', 'copy', 'decimal',
            'email', 'enum', 'fractions', 'ftplib', 'gzip', 'heapq', 'html', 'io',
            'ipaddress', 'keyword', 'locale', 'mimetypes', 'operator', 'pprint',
            'queue', 'secrets', 'smtplib', 'ssl', 'statistics', 'string', 'tarfile',
            'textwrap', 'token', 'tokenize', 'webbrowser', 'xml', 'zipfile', 'zlib'
        }
        return package in stdlib_packages
    
    def _cleanup(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception:
                pass  # 忽略清理失败