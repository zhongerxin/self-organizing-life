from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from .code_generator import CodeGenerator, GeneratedCode
from .execution_engine import VenvExecutionEngine, ExecutionResult

app = FastAPI(
    title="AI Python Code Interpreter",
    description="自动生成和执行Python代码的API服务",
    version="1.0.0"
)

# 初始化组件
code_generator = CodeGenerator()
execution_engine = VenvExecutionEngine()

class CodeRequest(BaseModel):
    request: str
    execute: bool = True

class CodeResponse(BaseModel):
    generated_code: str
    explanation: str
    dependencies: list[str]
    execution_result: Optional[dict] = None

@app.get("/")
async def root():
    return {"message": "AI Python Code Interpreter API", "version": "1.0.0"}

@app.post("/generate", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    """
    生成Python代码并可选择执行
    """
    try:
        # 生成代码
        generated = code_generator.generate_code(request.request)
        
        response_data = {
            "generated_code": generated.code,
            "explanation": generated.explanation,
            "dependencies": generated.dependencies,
            "execution_result": None
        }
        
        # 如果需要执行代码
        if request.execute:
            result = execution_engine.execute_code(generated.code)
            response_data["execution_result"] = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_time": result.execution_time,
                "exit_code": result.exit_code
            }
        
        return CodeResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

@app.post("/execute")
async def execute_code(code: str):
    """
    直接执行提供的Python代码
    """
    try:
        result = execution_engine.execute_code(code)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "exit_code": result.exit_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行代码时出错: {str(e)}")

@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "healthy", "service": "AI Python Code Interpreter"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)