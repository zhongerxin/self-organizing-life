import os
import sys
from datetime import datetime
from typing import Optional, IO
from contextlib import contextmanager
import re

class SessionLogger:
    def __init__(self, base_logs_dir: str = "logs"):
        self.base_logs_dir = base_logs_dir
        self.session_dir = None
        self.process_log_path = None
        self.generated_code_path = None
        self.original_stdout = None
        self.original_stderr = None
        self.log_file = None
        
    def create_session(self, user_request: str) -> str:
        """
        根据用户请求创建会话日志目录
        返回会话目录路径
        """
        # 确保logs目录存在
        os.makedirs(self.base_logs_dir, exist_ok=True)
        
        # 生成会话目录名称: 前10个字符 + 日期时分
        request_postfix = self._sanitize_filename(user_request[:10])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        session_name = f"{timestamp}_{request_postfix}"
        
        # 创建会话目录
        self.session_dir = os.path.join(self.base_logs_dir, session_name)
        os.makedirs(self.session_dir, exist_ok=True)
        
        # 设置文件路径
        self.process_log_path = os.path.join(self.session_dir, "process_log.txt")
        self.generated_code_path = os.path.join(self.session_dir, "generated_code.py")
        
        # 创建初始日志文件
        with open(self.process_log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== AI Python代码解释器会话日志 ===\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"用户请求: {user_request}\n")
            f.write(f"会话目录: {self.session_dir}\n")
            f.write("="*50 + "\n\n")
        
        return self.session_dir
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除多余的空格和特殊字符
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        # 确保不为空
        if not sanitized:
            sanitized = "request"
        return sanitized
    
    def log_message(self, message: str, category: str = "INFO"):
        """记录日志信息"""
        if not self.process_log_path:
            return
            
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{category}] {message}\n"
        
        with open(self.process_log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def save_generated_code(self, code: str, explanation: str = "", version: int = 1):
        """
        保存生成的Python代码
        
        Args:
            code: 代码内容
            explanation: 代码说明
            version: 代码版本号 (1=原始, 2=修复版本1, 3=修复版本2, ...)
        """
        if not self.session_dir:
            return
            
        # 生成文件名
        if version == 1:
            filename = "generated_code.py"
        else:
            filename = f"generated_code_{version}.py"
            
        filepath = os.path.join(self.session_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if explanation:
                f.write(f'"""\n{explanation}\n"""\n\n')
            f.write(code)
        
        # 更新生成代码路径引用
        if version == 1:
            self.generated_code_path = filepath
        
        return filepath
    
    @contextmanager
    def capture_output(self):
        """上下文管理器，捕获标准输出和错误输出到日志文件"""
        if not self.process_log_path:
            yield
            return
            
        class LogCapture:
            def __init__(self, log_path: str, original_stream: IO, stream_name: str):
                self.log_path = log_path
                self.original_stream = original_stream
                self.stream_name = stream_name
                
            def write(self, message: str):
                # 写入原始流
                self.original_stream.write(message)
                self.original_stream.flush()
                
                # 写入日志文件
                if message.strip():  # 只记录非空消息
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    log_entry = f"[{timestamp}] [{self.stream_name}] {message}"
                    if not message.endswith('\n'):
                        log_entry += '\n'
                    
                    try:
                        with open(self.log_path, 'a', encoding='utf-8') as f:
                            f.write(log_entry)
                    except Exception:
                        pass  # 忽略日志写入错误
                        
            def flush(self):
                self.original_stream.flush()
                
            def __getattr__(self, name):
                return getattr(self.original_stream, name)
        
        # 保存原始流
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            # 替换为日志捕获器
            sys.stdout = LogCapture(self.process_log_path, original_stdout, "STDOUT")
            sys.stderr = LogCapture(self.process_log_path, original_stderr, "STDERR")
            
            yield
            
        finally:
            # 恢复原始流
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    def log_execution_result(self, result, execution_time: float = None):
        """记录执行结果"""
        self.log_message("代码执行结果:", "RESULT")
        
        if hasattr(result, 'success'):
            # ExecutionResult对象
            self.log_message(f"执行状态: {'成功' if result.success else '失败'}")
            if result.output:
                self.log_message(f"输出: {result.output}")
            if result.error:
                self.log_message(f"错误: {result.error}")
            self.log_message(f"执行时间: {result.execution_time:.2f}秒")
            self.log_message(f"退出码: {result.exit_code}")
        else:
            # 其他类型的结果
            self.log_message(f"结果: {str(result)}")
            if execution_time:
                self.log_message(f"执行时间: {execution_time:.2f}秒")
    
    def log_step(self, step_name: str, details: str = ""):
        """记录执行步骤"""
        message = f"执行步骤: {step_name}"
        if details:
            message += f" - {details}"
        self.log_message(message, "STEP")
    
    def log_code_fix_attempt(self, attempt: int, error: str, fixed_code: str):
        """记录代码修复尝试"""
        self.log_message(f"代码修复尝试 #{attempt}", "FIX")
        self.log_message(f"原始错误: {error}", "ERROR")
        self.log_message(f"修复后代码长度: {len(fixed_code)} 字符", "FIX")
    
    def log_error(self, error: Exception, context: str = ""):
        """记录错误信息"""
        error_msg = f"错误发生在: {context}" if context else "发生错误"
        self.log_message(f"{error_msg}: {str(error)}", "ERROR")
    
    def finalize_session(self):
        """结束会话，写入总结信息"""
        if not self.process_log_path:
            return
            
        with open(self.process_log_path, 'a', encoding='utf-8') as f:
            f.write("\n" + "="*50 + "\n")
            f.write(f"会话结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"日志文件路径: {self.process_log_path}\n")
            f.write(f"生成代码路径: {self.generated_code_path}\n")
            f.write("="*50 + "\n")

# 全局日志实例
session_logger = SessionLogger()