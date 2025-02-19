import re
import time

from solution_methods.cp_sat.run_cp_sat import run_CP_SAT
from solution_methods.helper_functions import load_job_shop_env, load_parameters
from visualization import gantt_chart

if __name__ == '__main__':
    # freeze_support() # 关闭之后，貌似也能正常工作

    # 定义问题实例，也可以从配置文件中加载
    # problem_instance = "/fjsp/fattahi/MFJS10.fjs"
    problem_instance = "/fjsp/brandimarte/Mk10.fjs"
    # problem_instance = "/jsp/demirkol/rcmax_50_20_9.txt"

    start_time = time.time()

    # 加载作业车间环境
    jobShopEnv = load_job_shop_env(problem_instance)

    # 对初始作业车间环境绘制甘特图没有意义
    # plot_gantt_chart(jobShopEnv)

    # 加载CP_SAT配置
    parameters = load_parameters("configs/cp_sat.toml")

    makespan, jobShopEnv = run_CP_SAT(jobShopEnv, **parameters)

    # 使用正则表达式分割字符串
    instance = re.split(r'[/\.]', jobShopEnv.instance_name)

    # 检查是否有足够的部分，并处理边界条件
    title = instance[3] if len(instance) > 3 else "N/A"

    # 使用 f-string 提高可读性和性能.
    # print(f"{title}——CP_SAT——最小化最大完工时间——makespan:{makespan}"
    #
    print(f"{title}，CP-SAT，最小化最大完工时间，makespan:{makespan}，耗时:{time.time() - start_time}")

    gantt_chart.plot(jobShopEnv).show();
