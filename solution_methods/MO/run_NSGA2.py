import argparse  # 用于解析命令行参数
import datetime
import logging  # 用于日志记录
import os  # 用于处理文件和目录路径

from deap import tools  # 确保已导入 DEAP 库中的工具模块
from matplotlib import pyplot as plt

# 导入自定义模块
from solution_methods.GA.src.initialization import initialize_run  # 初始化遗传算法运行环境
from solution_methods.GA.src.operators import (
    evaluate_individual, evaluate_population, repair_precedence_constraints, variation
)  # 遗传算法操作函数
from solution_methods.GA.utils import record_stats, output_dir_exp_name, results_saving  # 工具函数：记录统计信息、生成输出目录、保存结果
from solution_methods.helper_functions import load_parameters, load_job_shop_env  # 辅助函数：加载参数和作业车间环境
from visualization import precedence_chart, gantt_chart

# 配置日志记录级别为 INFO
logging.basicConfig(level=logging.INFO)

# 默认参数文件路径
PARAM_FILE = "../../configs/GA.toml"


def run_NSGA2(jobShopEnv, population, toolbox, stats, pareto_front, **kwargs):
    """
    使用 NSGA-II 算法执行遗传算法，并返回最优解。

    参数:
        jobShopEnv: 调度问题的作业车间环境。
        population: 初始种群。
        toolbox: DEAP 工具箱，包含遗传算法的操作。
        stats: DEAP 统计对象，用于记录每代的统计信息。
        pareto_front: Pareto 最优解集。
        kwargs: 其他关键字参数，包括输出配置和算法参数。

    返回:
        最优解的适应度值及其对应的作业车间环境。
    """
    # 初始化当前代数和日志簿
    gen = 0
    logbook = tools.Logbook()  # 创建日志簿对象
    logbook.header = ["gen"] + (stats.fields if stats else [])  # 设置日志簿表头
    df_list = []  # 用于存储每代的统计数据

    # 记录初始种群的统计信息
    record_stats(gen, population, logbook, stats, kwargs['output']['logbook'], df_list, logging)
    if kwargs['output']['logbook']:
        logging.info(logbook.stream)  # 输出日志簿内容

    # 开始迭代进化过程
    for gen in range(1, kwargs['algorithm']['ngen'] + 1):  # ngen 为最大代数
        # 变异操作：生成后代种群
        offspring = variation(
            population, toolbox,
            pop_size=kwargs['algorithm'].get('population_size'),
            cr=kwargs['algorithm'].get('cr'),  # 交叉概率
            indpb=kwargs['algorithm'].get('indpb')  # 基因变异概率
        )

        # 如果环境中需要修复优先约束（适用于装配调度问题），则修复后代的优先约束
        if any(keyword in jobShopEnv.instance_name for keyword in ['/dafjs/', '/yfjs/']):
            try:
                offspring = repair_precedence_constraints(jobShopEnv, offspring)
            except Exception as e:
                logging.error(f"修复优先约束时出错: {e}")
                continue

        # 评估后代的适应度
        try:
            fitnesses = evaluate_population(toolbox, offspring)  # 计算每个个体的适应度
            for ind, fit in zip(offspring, fitnesses):
                ind.fitness.values = fit  # 将适应度值赋给个体
        except Exception as e:
            logging.error(f"评估后代适应度时出错: {e}")
            continue

        # 合并父代和子代，并使用 NSGA-II 的选择机制选择下一代种群
        combined_population = population + offspring
        population[:] = toolbox.select(combined_population, len(population))

        # 更新 Pareto 最优解集和统计信息
        pareto_front.update(population)
        record_stats(gen, population, logbook, stats, kwargs['output']['logbook'], df_list, logging)

    # 从 Pareto 最优解集中选择一个解（选择最小 makespan 的解）
    best_solution = min(pareto_front, key=lambda ind: ind.fitness.values[0])

    # 评估最佳个体的适应度值，并返回最终的作业车间环境
    fitnesses, jobShopEnv = evaluate_individual(best_solution, jobShopEnv, reset=False)

    # 绘制 Pareto 最优解集
    pareto_front_values = [ind.fitness.values for ind in pareto_front]
    makespans, balanced_workloads = zip(*pareto_front_values)
    plt.plot(makespans, balanced_workloads, color='red', marker='o',
             label='Pareto Front')  # 使用 plot 替换 scatter，并添加 marker
    plt.xlabel('Makespan')
    plt.ylabel('Balanced Workload')
    plt.title('Pareto Front Visualization')
    plt.legend()

    # 设置图像为 1:1 的比例
    plt.axis('equal')

    # 获取当前日期和时间，并格式化为文件名
    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pareto_front_{current_time}.svg'

    # 设置保存路径
    save_path = '/pareto_front'
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # 构建完整的文件路径
    full_filename = os.path.join(save_path, filename)

    # 保存为 SVG 文件
    plt.savefig(full_filename)
    plt.show()

    # 打印 Pareto 最优解集
    logging.info("Pareto 最优解集:")
    for ind in pareto_front:
        logging.info(f"个体适应度: {ind.fitness.values}")

    return fitnesses, jobShopEnv


def main(param_file=PARAM_FILE):
    """
    主函数，负责加载参数、初始化环境并运行遗传算法。

    参数:
        param_file: 参数文件路径。
    """
    try:
        parameters = load_parameters(param_file)  # 加载参数文件
        logging.info(f"成功从 {param_file} 加载参数。")
    except FileNotFoundError:
        logging.error(f"未找到参数文件 {param_file}。")
        return

    # 加载作业车间调度环境，并初始化遗传算法
    jobShopEnv = load_job_shop_env(parameters['instance'].get('problem_instance'))
    population, toolbox, stats, hof = initialize_run(jobShopEnv, **parameters)

    # 运行 NSGA-II 遗传算法
    fitnesses, jobShopEnv = run_NSGA2(jobShopEnv, population, toolbox, stats, hof, **parameters)

    if fitnesses is not None:
        # 检查输出配置并准备输出路径
        output_config = parameters['output']
        save_gantt = output_config.get('save_gantt')  # 是否保存甘特图
        save_results = output_config.get('save_results')  # 是否保存结果
        show_gantt = output_config.get('show_gantt')  # 是否显示甘特图
        show_precedences = output_config.get('show_precedences')  # 是否显示优先关系图

        if save_gantt or save_results:
            output_dir, exp_name = output_dir_exp_name(parameters)  # 生成输出目录和实验名称
            output_dir = os.path.join(output_dir, f"{exp_name}")
            os.makedirs(output_dir, exist_ok=True)  # 创建输出目录

        # 绘制优先关系图
        if show_precedences:
            precedence_chart.plot(jobShopEnv)

        # 绘制甘特图
        if show_gantt or save_gantt:
            logging.info("正在生成甘特图。")
            plt = gantt_chart.plot(jobShopEnv)
            if save_gantt:
                plt.savefig(os.path.join(output_dir, "gantt.png"))  # 保存甘特图为图片
                logging.info(f"甘特图已保存到 {output_dir}")
            if show_gantt:
                plt.show()  # 显示甘特图

        # 保存结果
        if save_results:
            results_saving(fitnesses, output_dir, parameters)
            logging.info(f"结果已保存到 {output_dir}")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行 NSGA-II 算法")
    parser.add_argument(
        "-f", "--config_file",
        type=str,
        default=PARAM_FILE,
        help="配置文件路径",
    )
    args = parser.parse_args()

    # 调用主函数并传入配置文件路径
    main(param_file=args.config_file)