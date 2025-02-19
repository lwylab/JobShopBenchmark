import os  # 导入os模块，用于文件和目录操作
import json  # 导入json模块，用于处理JSON数据
import datetime  # 导入datetime模块，用于处理日期和时间

from scheduling_environment.simulationEnv import SimulationEnv  # 从scheduling_environment.simulationEnv模块导入SimulationEnv类
from solution_methods.helper_functions import load_job_shop_env  # 从helper_functions模块导入加载作业车间环境的函数

# 定义默认结果保存根目录
DEFAULT_RESULTS_ROOT = os.getcwd() + "/results/dispatching_rules/"


def configure_simulation_env(jobShopEnv, **parameters):
    """
    根据参数配置模拟环境。

    参数:
    jobShopEnv (JobShop): 作业车间环境实例
    parameters: 其他参数，包括在线到达配置、作业车间实例等

    返回:
    simulationEnv (SimulationEnv): 配置好的模拟环境实例
    """
    # 创建SimulationEnv实例，根据参数设置是否为在线到达
    simulationEnv = SimulationEnv(online_arrivals=parameters['instance']['online_arrivals'])
    # 将作业车间环境实例赋值给模拟环境
    simulationEnv.jobShopEnv = jobShopEnv

    # 如果配置了在线到达，则设置在线到达的详细信息
    if parameters['instance']['online_arrivals']:
        simulationEnv.set_online_arrival_details(parameters['online_arrival_details'])
        # 设置作业车间环境中的机器数量
        simulationEnv.jobShopEnv.set_nr_of_machines(parameters['online_arrival_details']['number_total_machines'])

    return simulationEnv


def output_dir_exp_name(parameters):
    """
    根据参数生成输出目录和实验名称。

    参数:
    parameters: 包含输出配置和其他参数的字典

    返回:
    output_dir (str): 输出目录路径
    exp_name (str): 实验名称
    """
    # 检查是否提供了实验名称，如果没有则生成默认名称
    if 'experiment_name' in parameters['output'] and parameters['output']['experiment_name'] is not None:
        exp_name = parameters['output']['experiment_name']
    else:
        # 根据是否为在线到达生成不同的实例名称
        if parameters['instance']['online_arrivals']:
            instance_name = 'online_arrival_config'
        else:
            instance_name = parameters['instance']['problem_instance'].replace('/', '_')[1:]
            instance_name = instance_name.split('.')[0] if '.' in instance_name else instance_name
        # 获取调度规则和机器分配规则
        dispatching_rule = parameters['instance']['dispatching_rule']
        machine_assignment_rule = parameters['instance']['machine_assignment_rule']
        # 获取当前时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 生成实验名称
        exp_name = f"{instance_name}_{dispatching_rule}_{machine_assignment_rule}_{timestamp}"

    # 检查是否提供了输出目录，如果没有则使用默认目录
    if 'folder_name' in parameters['output'] and parameters['output']['folder_name'] is not None:
        output_dir = parameters['output']['folder_name']
    else:
        output_dir = DEFAULT_RESULTS_ROOT
    return output_dir, exp_name


def results_saving(makespan, path, parameters):
    """
    将调度规则调度结果保存到JSON文件。

    参数:
    makespan (float): 最大完成时间（makespan）
    path (str): 保存结果的目录路径
    parameters: 包含调度规则和其他参数的字典
    """
    # 根据是否为在线到达生成不同的结果字典
    if parameters['instance']['online_arrivals']:
        results = {
            "instance": parameters["instance"]["problem_instance"],
            "makespan": makespan,
            "dispatching_rule": parameters["instance"]["dispatching_rule"],
            "machine_assignment_rule": parameters["instance"]["machine_assignment_rule"],
            "number_total_machines": parameters["online_arrival_details"]["number_total_machines"],
            "inter_arrival_time": parameters["online_arrival_details"]["inter_arrival_time"],
            "simulation_time": parameters["online_arrival_details"]["simulation_time"],
            "min_nr_operations_per_job": parameters["online_arrival_details"]["min_nr_operations_per_job"],
            "max_nr_operations_per_job": parameters["online_arrival_details"]["max_nr_operations_per_job"],
            "min_duration_per_operation": parameters["online_arrival_details"]["min_duration_per_operation"],
            "max_duration_per_operation": parameters["online_arrival_details"]["max_duration_per_operation"]
        }
    else:
        results = {
            "instance": parameters["instance"]["problem_instance"],
            "makespan": makespan,
            "dispatching_rule": parameters["instance"]["dispatching_rule"],
            "machine_assignment_rule": parameters["instance"]["machine_assignment_rule"]
        }

    # 确保输出目录存在
    os.makedirs(path, exist_ok=True)

    # 生成结果文件路径
    file_path = os.path.join(path, "GA_results.json")
    # 将结果保存到JSON文件
    with open(file_path, "w") as outfile:
        json.dump(results, outfile, indent=4)
