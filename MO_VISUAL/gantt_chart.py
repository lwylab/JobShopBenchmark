import os
import re
from datetime import datetime

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from visualization.color_scheme import create_colormap


# 全局字体设置
def set_global_font(font_size=20):
    """
    设置全局字体样式和大小
    Args:
        font_size: 字体大小，默认为20
    """
    # 设置英文字体为Times New Roman
    english_font = 'Times New Roman'
    
    # 获取系统中所有可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 如果Times New Roman不可用，尝试使用其他英文字体
    if english_font not in available_fonts:
        english_alternatives = ['Arial', 'Helvetica', 'DejaVu Serif', 'DejaVu Sans']
        for font in english_alternatives:
            if font in available_fonts:
                english_font = font
                break
    
    # 设置所有字体为Times New Roman
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = [english_font, 'DejaVu Serif']
    
    # 解决负号显示问题
    plt.rcParams['axes.unicode_minus'] = False
    
    # 设置全局字体大小
    plt.rcParams['font.size'] = font_size
    plt.rcParams['axes.labelsize'] = font_size
    plt.rcParams['xtick.labelsize'] = font_size
    plt.rcParams['ytick.labelsize'] = font_size
    plt.rcParams['legend.fontsize'] = font_size
    plt.rcParams['axes.titlesize'] = font_size
    
    # 返回字体信息
    return {'english': english_font}


def plot(JobShop, font_size=20, save_dir=None):
    """
    绘制作业车间调度的甘特图。
    Args:
        JobShop: 作业车间调度环境对象。
        font_size: 字体大小，默认为20。
        save_dir: 保存甘特图的目录路径，默认为None（保存在当前目录）。
    Returns:
        Matplotlib绘图对象。
    """
    # 设置全局字体
    fonts = set_global_font(font_size)
    
    # 创建一个新的图形和坐标轴对象
    fig, ax = plt.subplots()

    # 从 color_scheme 模块中创建颜色映射，用于不同作业的颜色区分
    colormap = create_colormap()

    # 使用正则表达式分割实例名称字符串
    instance = re.split(r'[/.]', JobShop.instance_name)
    # 检查是否有足够的部分，并处理边界条件
    title = instance[3] if len(instance) > 3 else "N/A"

    # 格式化标题，包含实例名称和最大完工时间（makespan）
    initial_title = "Instance: " + title
    makespan_value = str(JobShop.makespan) if hasattr(JobShop, 'makespan') and JobShop.makespan is not None else "N/A"
    formatted_title = f"{initial_title}, Makespan: {makespan_value}"


    # 遍历 JobShop 中的每一台机器
    for machine in JobShop.machines:
        # 获取该机器处理过的所有操作，并按开始时间排序
        machine_operations = sorted(machine._processed_operations, key=lambda op: op.scheduling_information['start_time'])

        # 遍历该机器上的每一个操作
        for operation in machine_operations:
            # 获取操作的开始时间
            operation_start = operation.scheduling_information['start_time']

            # 获取操作的结束时间
            operation_end = operation.scheduling_information['end_time']

            # 计算操作的持续时间
            operation_duration = operation_end - operation_start

            # 获取操作的标识符
            operation_label = f"{operation.operation_id}"

            # 根据作业 ID 确定颜色索引
            color_index = operation.job_id % len(JobShop.jobs)

            # 如果颜色索引超出颜色映射范围，则取模以确保索引有效
            if color_index >= colormap.N:
                color_index = color_index % colormap.N

            # 获取对应的颜色
            color = colormap(color_index)

            # 绘制操作的时间段，使用指定的颜色
            ax.broken_barh(
                [(operation_start, operation_duration)],  # 时间段
                (machine.machine_id - 0.4, 0.8),  # 机器的位置（y 轴）
                facecolors=color,  # 填充颜色
                edgecolor='black'  # 边框颜色
            )

            # 获取操作的准备开始时间和准备时间
            setup_start = operation.scheduling_information['start_setup']
            setup_time = operation.scheduling_information['setup_time']

            # 如果有准备时间，则绘制准备时间段，使用灰色并添加斜线填充
            if setup_time is not None:
                ax.broken_barh(
                    [(setup_start, setup_time)],  # 时间段
                    (machine.machine_id - 0.4, 0.8),  # 机器的位置（y 轴）
                    facecolors='grey',  # 填充颜色
                    edgecolor='black',  # 边框颜色
                    hatch='/'  # 斜线填充
                )

            # 计算操作时间段的中间位置
            middle_of_operation = operation_start + operation_duration / 2

            # 在操作时间段的中间位置添加文本标签
            ax.text(
                middle_of_operation,  # x 轴位置
                machine.machine_id,  # y 轴位置
                operation_label,  # 标签文本
                ha='center',  # 水平对齐方式
                va='center',  # 垂直对齐方式
                fontsize=font_size * 0.8,  # 操作标签字体大小设为主字体的80%
                family='serif'  # 确保使用Times New Roman
            )

    # 设置图形的尺寸
    fig.set_size_inches(12, 6)

    # 设置 y 轴刻度和标签，表示机器编号
    ax.set_yticks(range(JobShop.nr_of_machines))
    ax.set_yticklabels([f'M{machine_id+1}' for machine_id in range(JobShop.nr_of_machines)])

    # 设置坐标轴标签，使用Times New Roman
    ax.set_xlabel('Time', family='serif')
    ax.set_ylabel('Machine', family='serif')

    # 设置图表标题，使用Times New Roman
    ax.set_title(formatted_title, family='serif')

    # 添加网格线
    # ax.grid(True)  # 注释掉或删除此行以去掉网格线

    # 自动保存图表
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 如果提供了保存目录，则使用该目录
    if save_dir:
        # 确保目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        filename = os.path.join(save_dir, f"{title}_gantt_{current_time}.svg")
    else:
        filename = f"{title}_gantt_{current_time}.svg"
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"甘特图已保存为 {filename}")

    # 返回绘制好的图表对象
    return plt
