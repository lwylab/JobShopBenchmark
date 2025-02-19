# GITHUB REPO: https://github.com/songwenas12/fjsp-drl

# 基于论文：
# "Flexible Job Shop Scheduling via Graph Neural Network and Deep Reinforcement Learning"
# by Wen Song, Xinyang Chen, Qiqiang Li and Zhiguang Cao
# 发表在 IEEE Transactions on Industrial Informatics, 2023.
# 论文URL: https://ieeexplore.ieee.org/document/9826438

import argparse  # 导入argparse模块，用于解析命令行参数
import logging  # 导入logging模块，用于记录日志信息
import os  # 导入os模块，用于文件和目录操作
import torch  # 导入torch模块，用于深度学习操作

from visualization import gantt_chart, precedence_chart  # 从visualization模块导入gantt_chart和precedence_chart模块，用于绘制甘特图和优先关系图
from solution_methods.helper_functions import load_job_shop_env, load_parameters, initialize_device, set_seeds  # 从helper_functions模块导入加载作业车间环境、加载参数、初始化设备和设置随机种子的函数
from solution_methods.FJSP_DRL.src.env_test import FJSPEnv_test  # 从env_test模块导入FJSPEnv_test类，用于测试环境
from scheduling_environment.simulationEnv import SimulationEnv  # 从scheduling_environment.simulationEnv模块导入SimulationEnv类

from solution_methods.FJSP_DRL.src.PPO import HGNNScheduler  # 从PPO模块导入HGNNScheduler类，用于图神经网络调度器
from solution_methods.FJSP_DRL.utils import output_dir_exp_name, results_saving  # 从utils模块导入生成输出目录名称和保存结果的函数
from solution_methods.FJSP_DRL.src.online_FJSP_DRL import run_online_dispatcher  # 从online_FJSP_DRL模块导入在线调度器函数

# 定义默认参数文件路径
PARAM_FILE = "../../configs/FJSP_DRL.toml"
# 配置日志级别为INFO，确保所有INFO级别的日志都会被记录
logging.basicConfig(level=logging.INFO)


def run_FJSP_DRL(jobShopEnv, **parameters):
    """
    运行FJSP_DRL算法。

    参数:
    jobShopEnv (JobShop): 作业车间环境实例
    parameters: 包含模型参数、测试参数和其他参数的字典

    返回:
    makespan (float): 最大完成时间（makespan）
    jobShopEnv (JobShop): 更新后的作业车间环境实例
    """
    # 设置设备和随机种子
    device = initialize_device(parameters)
    set_seeds(parameters["test_parameters"]["seed"])

    # 配置默认张量类型为设备类型
    torch.set_default_device('cuda' if device.type == 'cuda' else 'cpu')
    if device.type == 'cuda':
        torch.cuda.set_device(device)

    # 加载训练好的策略
    model_parameters = parameters["model_parameters"]
    test_parameters = parameters["test_parameters"]
    trained_policy = os.path.dirname(os.path.abspath(__file__)) + test_parameters['trained_policy']
    if trained_policy.endswith('.pt'):
        if device.type == 'cuda':
            policy = torch.load(trained_policy)
        else:
            policy = torch.load(trained_policy, map_location='cpu', weights_only=True)

        logging.info(f"训练好的策略已从 {test_parameters.get('trained_policy')} 加载。")
        model_parameters["actor_in_dim"] = model_parameters["out_size_ma"] * 2 + model_parameters["out_size_ope"] * 2
        model_parameters["critic_in_dim"] = model_parameters["out_size_ma"] + model_parameters["out_size_ope"]

        hgnn_model = HGNNScheduler(model_parameters).to(device)
        hgnn_model.load_state_dict(policy)

    if not parameters['test_parameters']['online_arrivals']:
        # 创建测试环境实例
        env_test = FJSPEnv_test(jobShopEnv, parameters["test_parameters"])
        state = env_test.state
        done = False

        # 生成实例的调度方案
        while not done:
            with torch.no_grad():
                actions = hgnn_model.act(state, [], done, flag_train=False, flag_sample=test_parameters['sample'])
            state, _, done = env_test.step(actions)
        makespan = env_test.JSP_instance.makespan

    else:
        # 创建模拟环境实例
        simulationEnv = SimulationEnv(
            online_arrivals=parameters["online_arrival_details"]
        )
        # 设置在线到达的详细信息
        simulationEnv.set_online_arrival_details(parameters["online_arrival_details"])
        # 设置作业车间环境中的机器数量
        simulationEnv.jobShopEnv.set_nr_of_machines(
            parameters["online_arrival_details"]["number_total_machines"]
        )
        # 将在线调度器添加到模拟环境中
        simulationEnv.simulator.process(
            run_online_dispatcher(
                simulationEnv, hgnn_model
            )
        )
        # 运行模拟直到配置的结束时间
        simulationEnv.simulator.run(
            until=parameters["online_arrival_details"]["simulation_time"]
        )
        makespan = simulationEnv.jobShopEnv.makespan
        jobShopEnv = simulationEnv.jobShopEnv

    return makespan, jobShopEnv


def main(param_file=PARAM_FILE):
    """
    主函数，负责加载参数文件并启动FJSP_DRL算法。

    参数:
    param_file (str): 参数文件路径，默认为PARAM_FILE
    """
    try:
        # 加载参数文件
        parameters = load_parameters(param_file)
    except FileNotFoundError:
        logging.error(f"未找到参数文件 {param_file}。")
        return

    # 加载作业车间环境实例
    jobShopEnv = load_job_shop_env(parameters['test_parameters']['problem_instance'])
    # 运行FJSP_DRL算法
    makespan, jobShopEnv = run_FJSP_DRL(jobShopEnv, **parameters)

    if makespan is not None:
        # 检查输出配置并准备输出路径（如果需要）
        output_config = parameters['test_parameters']
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
    parser = argparse.ArgumentParser(description="运行FJSP_DRL")
    parser.add_argument(
        "config_file",
        metavar='-f',
        type=str,
        nargs="?",
        default=PARAM_FILE,
        help="配置文件路径",
    )

    args = parser.parse_args()
    # 使用命令行参数中的配置文件路径调用主函数
    main(param_file=args.config_file)
