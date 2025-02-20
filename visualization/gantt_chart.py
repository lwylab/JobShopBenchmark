import matplotlib.pyplot as plt

from visualization.color_scheme import create_colormap


def plot(JobShop):
    # 创建一个新的图形和坐标轴对象
    fig, ax = plt.subplots()

    # 从 color_scheme 模块中创建颜色映射，用于不同作业的颜色区分
    colormap = create_colormap()

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
                fontsize=8  # 字体大小
            )

    # 设置图形的尺寸
    fig.set_size_inches(12, 6)

    # 设置 y 轴刻度和标签，表示机器编号
    ax.set_yticks(range(JobShop.nr_of_machines))
    ax.set_yticklabels([f'M{machine_id+1}' for machine_id in range(JobShop.nr_of_machines)])

    # 设置 x 轴标签为 "Time"
    ax.set_xlabel('Time')

    # 设置 y 轴标签为 "Machine"
    ax.set_ylabel('Machine')

    # 设置图表标题为 "Gantt Chart"
    ax.set_title('Gantt Chart')

    # 添加网格线
    ax.grid(True)

    # 返回绘制好的图表对象
    return plt
