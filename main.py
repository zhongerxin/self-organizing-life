#!/usr/bin/env python3

"""
AI Python代码解释器主程序入口
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import cli, interactive

if __name__ == '__main__':
    # 如果没有提供命令行参数，默认进入交互模式
    if len(sys.argv) == 1:
        interactive()
    else:
        cli()