import re
import time

from solution_methods.GA.run_NSGA2 import run_NSGA2
from solution_methods.GA.src.initialization import initialize_run
from solution_methods.helper_functions import load_job_shop_env, load_parameters
from visualization import gantt_chart

if __name__ == '__main__':
    # 遗传算法
    parameters = load_parameters("configs/GA.toml")
    jobShopEnv = load_job_shop_env(parameters['instance'].get('problem_instance'))

    population, toolbox, stats, pareto_front = initialize_run(jobShopEnv, **parameters)

    # 从此刻开始计时，，
    start_time = time.time()

    fitnesses, jobShopEnv = run_NSGA2(jobShopEnv, population, toolbox, stats, pareto_front, **parameters)

    # 使用正则表达式分割字符串
    instance = re.split(r'[/.]', jobShopEnv.instance_name)

    # 检查是否有足够的部分，并处理边界条件
    title = instance[3] if len(instance) > 3 else "N/A"

    # 使用 f-string 提高可读性和性能
    print(
        f"{title}——NSGA2算法——最大完工时间——makespan:{fitnesses[0]}——均衡工作负载——balanced_workload:{fitnesses[1]}——耗时:{time.time() - start_time}")

    gantt_chart.plot(jobShopEnv)
