from collections import defaultdict
from typing import Union, Tuple, Dict

# MySQL 设为可选依赖，缺失时自动降级为内存模式
try:
    from pymysql import Connection
    from pymysql.err import MySQLError
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False

__all__ = ['add_Classes', 'clean_table', 'plot_class_statistics']

def execute_db_operation(
        sql: str,
        params: Union[Tuple, Dict, None] = None,
        database: str = "steel",
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "123456",
) -> Union[int, None]:
    conn = None
    try:
        conn = Connection(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            affected_rows = cursor.execute(sql, params)
            return cursor.lastrowid or affected_rows

    except MySQLError as e:
        print(f"数据库错误({e.args[0]}): {e.args[1]}")
        return None
    except Exception as e:
        print(f"系统异常: {str(e)}")
        return None
    finally:
        if conn and conn.open:
            conn.close()

# 修复后的插入函数
def add_Classes(Class: str, Image_id: str, time: int, precise: int) -> int:
    """
    添加记录（无需手动指定ID）

    :param Class: 缺陷类别
    :param Image_id: 图像ID
    :param time: 时间戳
    :param precise: 准确度
    :return: 新插入的记录ID
    """
    # 确保 precise 是一个数值
    if precise is None:
        precise = 0.0

    insert_sql = """
    INSERT INTO steel 
        (Class, Image_id, time, precise)
    VALUES 
        (%(Class)s, %(Image_id)s, %(time)s, %(precise)s)
    """
    student_data = {
        'Class': Class,
        'Image_id': Image_id,
        'time': round(time, 4),
        'precise': round(precise, 4)
    }

    result = execute_db_operation(
        sql=insert_sql,
        params=student_data,
        database="steel"
    )

    # if result is not None:
    #     print(f"插入成功，记录ID: {result}")
    #     return result
    # else:
    #     raise ValueError("添加记录失败")

def clean_table():
    """
    清空 Steel 表中的所有数据
    """
    # 数据库连接配置
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'steel',
        'autocommit': True
    }

    try:
        # 创建数据库连接
        connection = pymysql.connect(**config)

        # 创建游标
        with connection.cursor() as cursor:
            # 清空表的 SQL 语句
            truncate_query = "TRUNCATE TABLE Steel;"

            # 执行清空表操作
            cursor.execute(truncate_query)

        print("表 Steel 中的数据已清空。")

    except MySQLError as e:
        print(f"数据库错误({e.args[0]}): {e.args[1]}")

    except Exception as e:
        print(f"系统异常: {str(e)}")

    finally:
        # 关闭数据库连接
        if connection and connection.open:
            connection.close()
            print("数据库连接已关闭。")


# 全局统计字典，用于记录各类别的出现次数
class_statistics = defaultdict(int)

def add_Classes(Class: str, Image_id: str, time: int, precise: float) -> int:
    """
    添加记录（无需手动指定ID）

    :param Class: 缺陷类别
    :param Image_id: 图像ID
    :param time: 时间戳
    :param precise: 准确度
    :return: 新插入的记录ID
    """
    # 确保 precise 是一个数值
    if precise is None:
        precise = 0.0

    # 更新类别统计
    class_statistics[Class] += 1

    insert_sql = """
    INSERT INTO steel 
        (Class, Image_id, time, precise)
    VALUES 
        (%(Class)s, %(Image_id)s, %(time)s, %(precise)s)
    """
    student_data = {
        'Class': Class,
        'Image_id': Image_id,
        'time': round(time, 4),
        'precise': round(precise, 4)
    }

    if MYSQL_AVAILABLE:
        result = execute_db_operation(
            sql=insert_sql,
            params=student_data,
            database="steel"
        )
        if result is not None:
            print(f"插入成功，记录ID: {result}")
            return result
        else:
            print("MySQL 写入失败，统计数据仅保存在内存中")
    else:
        print(f"MySQL 不可用，统计数据仅保存在内存中 (Class={Class})")
    return None

def plot_class_statistics():
    """
    绘制类别统计的柱状图（需要 matplotlib）
    """
    if not MPL_AVAILABLE:
        print("matplotlib 未安装，跳过图表绘制")
        return
    if not class_statistics:
        print("没有统计数据可供绘制。")
        return

    # 准备数据
    classes = list(class_statistics.keys())
    counts = list(class_statistics.values())

    # 创建柱状图
    plt.figure(figsize=(10, 6))
    plt.bar(classes, counts, color='skyblue')
    plt.xlabel('缺陷类别', fontsize=12)
    plt.ylabel('出现次数', fontsize=12)
    plt.title('检测到的类别统计', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # 显示图表
    plt.show()


# 模块级调用已移除（原 plot_class_statistics() 会导致导入时崩溃）