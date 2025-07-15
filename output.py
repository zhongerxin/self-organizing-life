# 简单的四则运算计算
def calculate():
    try:
        # 执行计算
        result = 32 * 24 - 23457
        print(f"32 * 24 - 23457 = {result}")
        return result
    except Exception as e:
        print(f"计算出错: {str(e)}")
        return None

if __name__ == "__main__":
    calculate()