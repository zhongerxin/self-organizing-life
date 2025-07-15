import os
import re
from typing import List, Dict, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class GeneratedCode:
    code: str
    explanation: str
    dependencies: List[str]

class CodeGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    def generate_code(self, user_request: str) -> GeneratedCode:
        prompt = f"""
你是一个Python代码生成助手。用户会提出一个需求，你需要生成对应的Python代码。

要求：
1. 生成的代码要完整可执行
2. 添加必要的注释
3. 如果需要第三方库，请在代码中使用import语句
4. 代码应该包含适当的错误处理

用户需求：{user_request}

请按以下格式回复：

```python
# 在这里写Python代码
```

DEPENDENCIES: package1,package2,package3 (如果不需要额外依赖，写 DEPENDENCIES: none)

EXPLANATION: 简要说明代码功能和实现思路
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=20000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return self._parse_response(content)
            
        except Exception as e:
            raise Exception(f"代码生成失败: {str(e)}")
    
    def fix_code_with_error(self, original_request: str, original_code: str, error_message: str, attempt: int = 1) -> GeneratedCode:
        """
        根据错误信息修复代码
        
        Args:
            original_request: 原始用户请求
            original_code: 原始代码
            error_message: 错误信息
            attempt: 修复尝试次数
        
        Returns:
            修复后的代码
        """
        prompt = f"""
你是一个Python代码修复助手。用户之前提出了一个需求，你生成了代码，但是执行时出现了错误。现在需要你分析错误并修复代码。

原始用户需求：{original_request}

之前生成的代码：
```python
{original_code}
```

执行时出现的错误：
{error_message}

请分析错误原因并修复代码。修复要求：
1. 仔细分析错误信息，找出根本原因
2. 生成修复后的完整代码
3. 添加更好的错误处理机制
4. 如果是第三方库的问题，考虑使用替代方案或更新的API
5. 确保代码能够正常运行

这是第{attempt}次修复尝试。

请按以下格式回复：

```python
# 在这里写修复后的Python代码
```

DEPENDENCIES: package1,package2,package3 (如果不需要额外依赖，写 DEPENDENCIES: none)

EXPLANATION: 详细说明错误原因和修复方案
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=20000,  # 增加token限制，因为需要分析更多内容
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return self._parse_response(content)
            
        except Exception as e:
            raise Exception(f"代码修复失败: {str(e)}")
    
    def _parse_response(self, content: str) -> GeneratedCode:
        # 提取Python代码块
        code_pattern = r'```python\n(.*?)\n```'
        code_match = re.search(code_pattern, content, re.DOTALL)
        code = code_match.group(1) if code_match else ""
        
        # 提取依赖列表
        deps_pattern = r'DEPENDENCIES:\s*(.+)'
        deps_match = re.search(deps_pattern, content)
        deps_str = deps_match.group(1).strip() if deps_match else "none"
        dependencies = [] if deps_str == "none" else [dep.strip() for dep in deps_str.split(",")]
        
        # 提取说明
        explanation_pattern = r'EXPLANATION:\s*(.+)'
        explanation_match = re.search(explanation_pattern, content, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else "无说明"
        
        return GeneratedCode(
            code=code,
            explanation=explanation,
            dependencies=dependencies
        )
    
    def analyze_dependencies(self, code: str) -> List[str]:
        """从代码中提取import的包名"""
        import_pattern = r'^(?:from\s+(\w+)|import\s+(\w+))'
        imports = re.findall(import_pattern, code, re.MULTILINE)
        
        packages = set()
        for from_import, direct_import in imports:
            package = from_import or direct_import
            # 过滤标准库
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
            'glob', 'platform', 'warnings', 'traceback', 'inspect', 'typing'
        }
        return package in stdlib_packages