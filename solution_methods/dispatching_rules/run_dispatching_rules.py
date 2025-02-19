import argparse  # 导入argparse模块，用于解析命令行参数
import logging  # 导入logging模块，用于记录日志信息
import os  # 导入os模块，用于文件和目录操作

from scheduling_environment.jobShop import JobShop  # 从scheduling_environment.jobShop模块导入JobShop类
from visualization import gantt_chart, precedence_chart  # 从visualization模块导入gantt_chart和precedence_chart模块，用于绘制甘特图和优先关系图
from solution_methods.dispatching_rules.utils import configure_simulation_env, output_dir_exp_name, results_saving  # 从utils模块导入配置模拟环境、生成输出目录名称和保存结果的函数
from solution_methods.helper_functions import load_parameters, load_job_shop_env  # 从helper_functions模块导入加载参数和加载作业车间环境的函数
from solution_methods.dispatching_rules.src.scheduling_functions import scheduler  # 从scheduling_functions模块导入调度器函数

# 配置日志级别为INFO，确保所有INFO级别的日志都会被记录
logging.basicConfig(level=logging.INFO)

# 定义默认参数文件路径
PARAM_FILE = "../../configs/dispatching_rules.toml"


def run_dispatching_rules(jobShopEnv, **kwargs):
    """
    执行调度规则算法。

    参数:
    jobShopEnv (JobShop): 作业车间环境实例
    kwargs: 其他参数，包括调度规则、机器分配规则等

    返回:
    makespan (float): 最大完成时间（makespan）
    jobShopEnv (JobShop): 更新后的作业车间环境实例
    """

    # 获取调度规则和机器分配规则
    dispatching_rule = kwargs['instance']['dispatching_rule']
    machine_assignment_rule = kwargs['instance']['machine_assignment_rule']

    # 如果调度规则是SPT且机器分配规则不是SPT，则抛出错误
    if dispatching_rule == 'SPT' and machine_assignment_rule != 'SPT':
        raise ValueError("SPT调度规则需要SPT机器分配规则。")

    # 配置模拟环境
    simulationEnv = configure_simulation_env(jobShopEnv, **kwargs)

    # 将调度器添加到模拟环境中
    simulationEnv.simulator.process(scheduler(simulationEnv, **kwargs))

    # 对于在线到达的情况，运行模拟直到配置的结束时间
    if kwargs['instance']['online_arrivals']:
        simulationEnv.simulator.run(until=kwargs['online_arrival_details']['simulation_time'])
    # 对于静态实例，运行模拟直到所有操作都被调度
    else:
        simulationEnv.simulator.run()

    # 获取最大完成时间（makespan）
    makespan = simulationEnv.jobShopEnv.makespan
    logging.info(f"Makespan: {makespan}")

    return makespan, simulationEnv.jobShopEnv


def main(param_file: str = PARAM_FILE):
    """
    主函数，负责加载参数文件并启动调度规则算法。

    参数:
    param_file (str): 参数文件路径，默认为PARAM_FILE
    """

    try:
        # 加载参数文件
        parameters = load_parameters(param_file)
    except FileNotFoundError:
        logging.error(f"未找到参数文件 {param_file}。")
        return

    # 根据是否配置了在线到达来配置模拟环境
    if parameters['instance']['online_arrivals']:
        jobShopEnv = JobShop()  # 创建一个新的作业车间环境实例
        makespan, jobShopEnv = run_dispatching_rules(jobShopEnv, **parameters)
        logging.warning(f"对于配置了'在线到达'的问题，最大完成时间目标无关紧要。")
    else:
        # 加载现有的作业车间环境实例
        jobShopEnv = load_job_shop_env(parameters['instance'].get('problem_instance'))
        makespan, jobShopEnv = run_dispatching_rules(jobShopEnv, **parameters)

    if makespan is not None:
        # 检查输出配置并准备输出路径（如果需要）
        output_config = parameters['output']
        save_gantt = output_config.get('save_gantt')
        save_results = output_config.get('save_results')
        show_gantt = output_config.get('show_gantt')
        show_precedences = output_config.get('show_precedences')

        # 如果需要保存甘特图或结果，则创建输出目录
        if save_gantt or save_results:
            output_dir, exp_name = output_dir_exp_name(parameters)
            output_dir = os.path.join(output_dir, f"{exp_name}")
            os.makedirs(output_dir, exist_ok=True)

        # 如果需要显示优先关系图，则绘制优先关系图
        if show_precedences:
            precedence_chart.plot(jobShopEnv)

        # 如果需要显示或保存甘特图，则生成甘特图
        if show_gantt or save_gantt:
            logging.info("正在生成甘特图。")
            plt = gantt_chart.plot(jobShopEnv)

            # 如果需要保存甘特图，则保存到指定路径
            if save_gantt:
                plt.savefig(output_dir + "/gantt.png")
                logging.info(f"甘特图已保存到 {output_dir}")

            # 如果需要显示甘特图，则显示图表
            if show_gantt:
                plt.show()

        # 如果启用了保存结果，则保存结果到指定路径
        if save_results:
            results_saving(makespan, output_dir, parameters)
            logging.info(f"结果已保存到 {output_dir}")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行调度规则。")
    parser.add_argument(
        "-f",
        "--config_file",
        type=str,
        default=PARAM_FILE,
        help="配置文件路径",
    )

    args = parser.parse_args()
    main(param_file=args.config_file)  # 使用命令行参数中的配置文件路径调用主函数
