import re
import time

from solution_methods.dispatching_rules.run_dispatching_rules import run_dispatching_rules
from solution_methods.helper_functions import load_job_shop_env, load_parameters
from visualization import gantt_chart

if __name__ == '__main__':

    problem_instance = "/fjsp/brandimarte/Mk10.fjs"

    # 加载作业车间环境
    jobShopEnv = load_job_shop_env(problem_instance)


    # 加载CP_SAT配置
    parameters = load_parameters("configs/dispatching_rules.toml")

    # 从此刻开始计时
    start_time = time.time()

    makespan, jobShopEnv = run_dispatching_rules(jobShopEnv, **parameters)

    # 使用正则表达式分割字符串
    instance = re.split(r'[/.]', jobShopEnv.instance_name)

    # 检查是否有足够的部分，并处理边界条件
    title = instance[3] if len(instance) > 3 else "N/A"

    print(f"{title}，调度规则，最小化最大完工时间，makespan:{makespan}，耗时:{time.time() - start_time}")

    gantt_chart.plot(jobShopEnv).show();
