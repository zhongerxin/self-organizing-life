# AI Python代码解释器

一个基于Claude AI的Python代码自动生成和执行系统。用户可以通过自然语言描述需求，系统会自动生成相应的Python代码，在虚拟环境中执行，并自动安装所需的依赖包。

## 功能特性

- 🤖 **自然语言转代码**: 使用Claude AI根据自然语言描述生成Python代码
- 🔧 **自动依赖管理**: 自动检测和安装代码所需的第三方包
- 🏃 **安全执行环境**: 在独立的虚拟环境中执行代码
- 📊 **详细执行结果**: 提供代码输出、错误信息和执行时间
- 🌐 **多种使用方式**: 支持CLI命令行、交互式模式和Web API

## 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加你的Claude API密钥
# ANTHROPIC_API_KEY=your_claude_api_key_here
```

### 3. 开始使用

#### 快速开始（推荐）
```bash
# 直接运行，默认进入交互模式
python main.py
```

#### CLI模式
```bash
# 生成并执行代码
python main.py generate "写一个计算斐波那契数列的函数"

# 只生成代码，不执行
python main.py generate "创建一个简单的HTTP服务器" --no-execute

# 保存生成的代码到文件
python main.py generate "计算下 32 * 24 - 23457 等于多少 " --save output.py
```

#### 交互式模式
```bash
python main.py interactive
```

#### Web API模式
```bash
# 启动API服务器
python main.py server

# 访问 http://localhost:8000/docs 查看API文档
```

## 使用示例

### 示例1: 数据分析
```bash
python main.py generate "读取CSV文件，计算平均值并生成柱状图"
```

### 示例2: 文件操作
```bash
python main.py generate "遍历当前目录的所有Python文件，统计代码行数"
```

### 示例3: API调用
```bash
python main.py generate "调用天气API获取北京天气信息"
```

## API接口

### POST /generate
生成并可选择执行Python代码

**请求体:**
```json
{
  "request": "你的需求描述",
  "execute": true
}
```

**响应:**
```json
{
  "generated_code": "生成的Python代码",
  "explanation": "代码说明",
  "dependencies": ["依赖包列表"],
  "execution_result": {
    "success": true,
    "output": "执行输出",
    "error": "",
    "execution_time": 1.23,
    "exit_code": 0
  }
}
```

### POST /execute
直接执行提供的Python代码

**请求参数:**
- `code`: Python代码字符串

## 项目结构

```
self-organizing-life/
├── venv/                   # Python虚拟环境
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── code_generator.py   # 代码生成模块
│   ├── execution_engine.py # 代码执行引擎
│   ├── main.py            # FastAPI应用
│   └── cli.py             # CLI界面
├── tests/                  # 测试文件
├── docs/                   # 文档目录
│   └── project-plan.md    # 项目计划
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量模板
├── .gitignore            # Git忽略文件
├── main.py               # 程序入口
└── README.md             # 项目说明
```

## 技术架构

```
用户请求 → 代码生成 → venv环境执行 → 依赖自动安装 → 结果返回
```

### 核心组件

- **CodeGenerator**: 使用Claude API生成Python代码
- **VenvExecutionEngine**: 在虚拟环境中执行代码并管理依赖
- **FastAPI**: 提供RESTful API接口
- **Click**: 提供命令行界面

## 安全考虑

- 代码在独立的虚拟环境中执行
- 执行时间限制（防止无限循环）
- 自动依赖检测和安装
- 临时文件自动清理

## 开发说明

### 添加新功能
1. 在相应模块中添加功能代码
2. 更新CLI命令（如需要）
3. 添加API端点（如需要）
4. 编写测试用例

### 测试
```bash
# 运行测试
python -m pytest tests/

# 测试覆盖率
python -m pytest --cov=src tests/
```

## 常见问题

**Q: 如何获取Claude API密钥？**
A: 访问 https://console.anthropic.com/ 注册账号并创建API密钥。

**Q: 代码执行失败怎么办？**
A: 检查生成的代码是否正确，确认依赖包是否安装成功，查看错误信息进行调试。

**Q: 如何添加自定义的包到标准库列表？**
A: 编辑 `execution_engine.py` 中的 `_is_stdlib` 方法，添加包名到 `stdlib_packages` 集合。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！