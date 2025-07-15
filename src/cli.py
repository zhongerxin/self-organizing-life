import click
import os
import sys
from .code_generator import CodeGenerator
from .execution_engine import VenvExecutionEngine
from .logger import session_logger

@click.group()
def cli():
    """AI Python代码解释器 - 自动生成和执行Python代码"""
    pass

@cli.command()
@click.argument('request')
@click.option('--no-execute', is_flag=True, help='只生成代码，不执行')
@click.option('--save', type=str, help='保存生成的代码到文件')
def generate(request, no_execute, save):
    """
    根据自然语言请求生成Python代码
    
    REQUEST: 你的需求描述，比如 "写一个计算斐波那契数列的函数"
    """
    # 创建会话日志
    session_dir = session_logger.create_session(request)
    
    try:
        # 检查环境变量
        if not os.getenv("ANTHROPIC_API_KEY"):
            session_logger.log_error(Exception("ANTHROPIC_API_KEY未设置"), "环境检查")
            click.echo("❌ 错误: 请设置 ANTHROPIC_API_KEY 环境变量", err=True)
            click.echo("提示: 复制 .env.example 为 .env 并填入你的API密钥", err=True)
            sys.exit(1)
        
        session_logger.log_step("开始生成代码", f"用户请求: {request}")
        
        # 使用日志捕获输出
        with session_logger.capture_output():
            click.echo(f"🤖 正在为您生成代码: {request}")
            
            # 初始化代码生成器
            generator = CodeGenerator()
            
            # 生成代码
            with click.progressbar(length=100, label='生成中...') as bar:
                generated = generator.generate_code(request)
                bar.update(100)
            
            session_logger.log_step("代码生成完成", f"生成了{len(generated.code)}个字符的代码")
            
            # 保存生成的代码到日志
            session_logger.save_generated_code(generated.code, generated.explanation)
            
            click.echo("\n" + "="*50)
            click.echo("📝 生成的代码:")
            click.echo("="*50)
            click.echo(generated.code)
            
            click.echo("\n" + "="*50)
            click.echo("💡 代码说明:")
            click.echo("="*50)
            click.echo(generated.explanation)
            
            if generated.dependencies:
                click.echo(f"\n📦 需要的依赖包: {', '.join(generated.dependencies)}")
                session_logger.log_step("检测到依赖", f"依赖包: {', '.join(generated.dependencies)}")
            
            # 保存代码到文件
            if save:
                with open(save, 'w', encoding='utf-8') as f:
                    f.write(generated.code)
                click.echo(f"💾 代码已保存到: {save}")
                session_logger.log_step("保存代码文件", f"保存到: {save}")
            
            # 执行代码
            if not no_execute:
                click.echo("\n" + "="*50)
                click.echo("🚀 执行结果:")
                click.echo("="*50)
                
                session_logger.log_step("开始执行代码")
                
                executor = VenvExecutionEngine()
                
                with click.progressbar(length=100, label='执行中...') as bar:
                    # 使用带重试的执行方法
                    result, final_code, attempts = executor.execute_with_retry(
                        generated.code, generator, request, max_retries=2
                    )
                    bar.update(100)
                
                # 如果代码被修复过，保存修复后的版本
                if final_code != generated.code:
                    session_logger.save_generated_code(final_code, f"修复后的代码（第{attempts}次尝试）", version=attempts)
                    session_logger.log_step("代码修复", f"经过{attempts}次尝试后的最终代码已保存")
                
                # 记录执行结果
                session_logger.log_execution_result(result)
                
                if result.success:
                    click.echo("✅ 执行成功!")
                    if attempts > 1:
                        click.echo(f"💡 代码经过{attempts - 1}次修复后成功执行")
                    if result.output:
                        click.echo("输出:")
                        click.echo(result.output)
                else:
                    click.echo("❌ 执行失败!")
                    if attempts > 1:
                        click.echo(f"💡 代码经过{attempts - 1}次修复尝试仍然失败")
                    if result.error:
                        click.echo("错误信息:")
                        click.echo(result.error, err=True)
                
                click.echo(f"⏱️  执行时间: {result.execution_time:.2f}秒")
            
            click.echo(f"\n📁 会话日志已保存到: {session_dir}")
        
    except Exception as e:
        session_logger.log_error(e, "generate命令执行")
        click.echo(f"❌ 发生错误: {str(e)}", err=True)
        sys.exit(1)
    finally:
        session_logger.finalize_session()

@cli.command()
@click.argument('file_path')
def execute(file_path):
    """
    执行指定的Python文件
    
    FILE_PATH: Python文件路径
    """
    # 创建会话日志
    session_dir = session_logger.create_session(f"执行文件: {os.path.basename(file_path)}")
    
    try:
        if not os.path.exists(file_path):
            session_logger.log_error(Exception(f"文件不存在: {file_path}"), "文件检查")
            click.echo(f"❌ 文件不存在: {file_path}", err=True)
            sys.exit(1)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        session_logger.log_step("读取文件", f"文件路径: {file_path}, 代码长度: {len(code)}")
        
        # 保存执行的代码到日志
        session_logger.save_generated_code(code, f"执行文件: {file_path}")
        
        with session_logger.capture_output():
            click.echo(f"🚀 执行文件: {file_path}")
            
            session_logger.log_step("开始执行代码")
            
            executor = VenvExecutionEngine()
            generator = CodeGenerator()
            
            with click.progressbar(length=100, label='执行中...') as bar:
                # 使用带重试的执行方法
                result, final_code, attempts = executor.execute_with_retry(
                    code, generator, f"执行文件: {file_path}", max_retries=2
                )
                bar.update(100)
            
            # 如果代码被修复过，保存修复后的版本
            if final_code != code:
                session_logger.save_generated_code(final_code, f"修复后的代码（第{attempts}次尝试）", version=attempts)
                session_logger.log_step("代码修复", f"经过{attempts}次尝试后的最终代码已保存")
            
            # 记录执行结果
            session_logger.log_execution_result(result)
            
            click.echo("\n" + "="*50)
            click.echo("🚀 执行结果:")
            click.echo("="*50)
            
            if result.success:
                click.echo("✅ 执行成功!")
                if attempts > 1:
                    click.echo(f"💡 代码经过{attempts - 1}次修复后成功执行")
                if result.output:
                    click.echo("输出:")
                    click.echo(result.output)
            else:
                click.echo("❌ 执行失败!")
                if attempts > 1:
                    click.echo(f"💡 代码经过{attempts - 1}次修复尝试仍然失败")
                if result.error:
                    click.echo("错误信息:")
                    click.echo(result.error, err=True)
            
            click.echo(f"⏱️  执行时间: {result.execution_time:.2f}秒")
            click.echo(f"\n📁 会话日志已保存到: {session_dir}")
        
    except Exception as e:
        session_logger.log_error(e, "execute命令执行")
        click.echo(f"❌ 发生错误: {str(e)}", err=True)
        sys.exit(1)
    finally:
        session_logger.finalize_session()

@cli.command()
def server():
    """启动FastAPI服务器"""
    try:
        import uvicorn
        click.echo("🌐 启动AI Python代码解释器服务器...")
        click.echo("📍 服务地址: http://localhost:8000")
        click.echo("📚 API文档: http://localhost:8000/docs")
        click.echo("按 Ctrl+C 停止服务")
        
        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
        
    except KeyboardInterrupt:
        click.echo("\n👋 服务器已停止")
    except Exception as e:
        click.echo(f"❌ 启动服务器失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def interactive():
    """交互式模式"""
    try:
        # 检查环境变量
        if not os.getenv("ANTHROPIC_API_KEY"):
            click.echo("❌ 错误: 请设置 ANTHROPIC_API_KEY 环境变量", err=True)
            click.echo("提示: 复制 .env.example 为 .env 并填入你的API密钥", err=True)
            sys.exit(1)
        
        click.echo("🤖 AI Python代码解释器 - 交互式模式")
        click.echo("输入你的需求，输入 'quit' 或 'exit' 退出")
        click.echo("="*50)
        
        generator = CodeGenerator()
        executor = VenvExecutionEngine()
        
        while True:
            try:
                request = click.prompt("\n💭 请描述你的需求", type=str)
                
                if request.lower() in ['quit', 'exit', 'q']:
                    click.echo("👋 再见!")
                    break
                
                # 为每个交互创建会话日志
                session_dir = session_logger.create_session(request)
                
                try:
                    session_logger.log_step("交互式模式 - 开始生成代码", f"用户请求: {request}")
                    
                    with session_logger.capture_output():
                        # 生成代码
                        click.echo("🤖 正在生成代码...")
                        generated = generator.generate_code(request)
                        
                        session_logger.log_step("代码生成完成", f"生成了{len(generated.code)}个字符的代码")
                        
                        # 保存生成的代码到日志
                        session_logger.save_generated_code(generated.code, generated.explanation)
                        
                        click.echo("\n📝 生成的代码:")
                        click.echo("-" * 30)
                        click.echo(generated.code)
                        
                        click.echo(f"\n💡 {generated.explanation}")
                        
                        if generated.dependencies:
                            click.echo(f"📦 依赖: {', '.join(generated.dependencies)}")
                            session_logger.log_step("检测到依赖", f"依赖包: {', '.join(generated.dependencies)}")
                        
                        # 询问是否执行
                        if click.confirm("🚀 是否执行这段代码?", default=True):
                            click.echo("执行中...")
                            session_logger.log_step("开始执行代码")
                            
                            # 使用带重试的执行方法
                            result, final_code, attempts = executor.execute_with_retry(
                                generated.code, generator, request, max_retries=2
                            )
                            
                            # 如果代码被修复过，保存修复后的版本
                            if final_code != generated.code:
                                session_logger.save_generated_code(final_code, f"修复后的代码（第{attempts}次尝试）", version=attempts)
                                session_logger.log_step("代码修复", f"经过{attempts}次尝试后的最终代码已保存")
                            
                            # 记录执行结果
                            session_logger.log_execution_result(result)
                            
                            if result.success:
                                click.echo("✅ 执行成功!")
                                if attempts > 1:
                                    click.echo(f"💡 代码经过{attempts - 1}次修复后成功执行")
                                if result.output:
                                    click.echo("输出:")
                                    click.echo(result.output)
                            else:
                                click.echo("❌ 执行失败!")
                                if attempts > 1:
                                    click.echo(f"💡 代码经过{attempts - 1}次修复尝试仍然失败")
                                if result.error:
                                    click.echo("错误:")
                                    click.echo(result.error)
                            
                            click.echo(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
                        
                        click.echo(f"📁 会话日志已保存到: {session_dir}")
                
                except Exception as e:
                    session_logger.log_error(e, "交互式模式单次执行")
                    click.echo(f"❌ 发生错误: {str(e)}", err=True)
                finally:
                    session_logger.finalize_session()
                
            except KeyboardInterrupt:
                click.echo("\n👋 再见!")
                break
            except Exception as e:
                click.echo(f"❌ 发生错误: {str(e)}", err=True)
                
    except Exception as e:
        click.echo(f"❌ 启动交互模式失败: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()