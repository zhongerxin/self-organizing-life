# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Python Code Interpreter that generates and executes Python code based on natural language requests. Users can describe what they want in Chinese or English, and the system will generate Python code, automatically install dependencies, and execute the code in a virtual environment.

## Development Setup

### Required Environment Setup
- Python virtual environment must be activated: `source venv/bin/activate`
- Claude API key must be set: `cp .env.example .env` and add `ANTHROPIC_API_KEY`
- Install dependencies: `pip install -r requirements.txt`

### Running the Application
- Quick start: `python main.py` (defaults to interactive mode)
- CLI mode: `python main.py generate "your request"`
- Interactive mode: `python main.py interactive`
- Web server: `python main.py server` (FastAPI on port 8000)
- Execute files: `python main.py execute filepath.py`

### Testing
- Run tests: `python -m pytest tests/`
- Test with coverage: `python -m pytest --cov=src tests/`

## Architecture

The system follows a pipeline architecture:
```
用户请求 → 代码生成 → venv环境执行 → 依赖自动安装 → 结果返回
```

### Core Components

**CodeGenerator (`src/code_generator.py`)**
- Uses Anthropic Claude API to generate Python code from natural language
- Parses AI responses to extract code, dependencies, and explanations
- Structured prompt engineering for consistent output format
- Maintains stdlib package list to filter dependencies

**VenvExecutionEngine (`src/execution_engine.py`)**
- Executes generated code in the project's virtual environment
- Automatically detects and installs third-party dependencies via pip
- Creates temporary script files for execution
- Handles timeouts, errors, and cleanup
- Cross-platform support (Windows/macOS/Linux)

**FastAPI Application (`src/main.py`)**
- RESTful API with `/generate` and `/execute` endpoints
- Pydantic models for request/response validation
- Integrates CodeGenerator and VenvExecutionEngine
- Error handling and structured responses

**CLI Interface (`src/cli.py`)**
- Click-based command-line interface
- Multiple modes: generate, execute, server, interactive
- Progress bars and colored output
- File saving capabilities

## Key Technical Details

### Dependency Management
- Both CodeGenerator and VenvExecutionEngine maintain stdlib package lists
- Automatic pip installation in virtual environment
- 5-minute timeout for package installation
- Dependency extraction via regex parsing of import statements

### Code Execution Safety
- All code runs in isolated virtual environment
- 60-second execution timeout
- Temporary file cleanup after execution
- Process isolation via subprocess

### Auto-Fix Mechanism
- When code execution fails, system automatically attempts to fix errors
- Uses `CodeGenerator.fix_code_with_error()` to analyze and repair code
- Maximum 2 retry attempts per execution
- Each fix attempt saves a new version: `generated_code_2.py`, `generated_code_3.py`
- Fixed code versions include detailed error analysis and repair explanation

### AI Integration
- Uses Claude 3.5 Sonnet model
- Structured prompt with specific output format requirements
- Response parsing expects: code blocks, DEPENDENCIES line, EXPLANATION line
- Error handling for API failures

## Logging System

The project includes comprehensive session logging that automatically captures all user interactions:

**SessionLogger (`src/logger.py`)**
- Creates unique session directories: `logs/{request_prefix}_{YYYYMMDD_HHMM}/`
- Generates `process_log.txt` with timestamped execution logs
- Saves `generated_code.py` with the AI-generated Python code
- Saves `generated_code_2.py`, `generated_code_3.py` etc. for auto-fixed versions
- Captures stdout/stderr during execution
- Automatically used by all CLI commands

**Log Directory Structure:**
```
logs/
├── 写一个计算器_20250715_1430/
│   ├── process_log.txt       # Complete execution log
│   ├── generated_code.py     # Original generated code
│   └── generated_code_2.py   # First auto-fix attempt (if needed)
└── 数据分析_20250715_1445/
    ├── process_log.txt
    ├── generated_code.py
    ├── generated_code_2.py     # Auto-fixed version
    └── generated_code_3.py     # Second auto-fix attempt
```

## Common Development Patterns

### Adding New CLI Commands
1. Add command function to `src/cli.py` with `@cli.command()` decorator
2. Create session with `session_logger.create_session(request)`
3. Use `session_logger.capture_output()` context manager
4. Call `session_logger.finalize_session()` in finally block
5. Use consistent error handling patterns with try/except

### Extending API Endpoints
1. Add new endpoint to `src/main.py`
2. Create Pydantic models for request/response if needed
3. Use existing error handling pattern with HTTPException
4. Document endpoint with docstring

### Modifying Code Generation
1. Update prompt in CodeGenerator.generate_code()
2. Adjust response parsing in _parse_response() if format changes
3. Update stdlib package list in _is_stdlib() as needed
4. Test with various request types

## Important Notes

- The system expects Chinese prompts but works with English
- Virtual environment path is configurable via VenvExecutionEngine constructor
- Temporary files are automatically cleaned up after execution
- All components are designed to be stateless and thread-safe
- Error messages are localized in Chinese