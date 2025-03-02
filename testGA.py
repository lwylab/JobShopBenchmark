import json
import re
import time

from solution_methods.GA.run_GA import run_GA
from solution_methods.GA.src.initialization import initialize_run
from solution_methods.helper_functions import load_job_shop_env, load_parameters
from visualization import gantt_chart

if __name__ == '__main__':
    # freeze_support() # 关闭之后，貌似也能正常工作。
    #

    # 遗传算法
    parameters = load_parameters("configs/GA.toml")
    jobShopEnv = load_job_shop_env(parameters['instance'].get('problem_instance'))

    # problem_instance = "/jsp/demirkol/rcmax_50_20_9.txt"

    # problem_instance = "/fjsp/brandimarte/Mk10.fjs"

    # 加载作业车间环境
    # jobShopEnv = load_job_shop_env(problem_instance)

    # 画析构图
    # draw_precedence_relations(jobShopEnv)

    population, toolbox, stats, hof = initialize_run(jobShopEnv, **parameters)

    # 从此刻开始计时
    start_time = time.time()

    makespan, jobShopEnv = run_GA(jobShopEnv, population, toolbox, stats, hof, **parameters)

    # 使用正则表达式分割字符串
    instance = re.split(r'[/.]', jobShopEnv.instance_name)

    # 检查是否有足够的部分，并处理边界条件
    title = instance[3] if len(instance) > 3 else "N/A"

    # 使用 f-string 提高可读性和性能
    print(f"{title}，GA算法，最小化最大完工时间，makespan:{makespan}，耗时:{time.time() - start_time}")

    # print(jobShopEnv)
    # print(jobShopEnv.jobs)
    # print(jobShopEnv.machines)

    gantt_chart.plot(jobShopEnv).show()

    # o = jobShopEnv.operations

    result = []
    for op in jobShopEnv.operations:
        row = op.scheduling_information  # 这是一个dict
        row.update({'job_id': op.job_id, 'operation_id': op.operation_id})
        result.append(row)


    # 将 result 转换为 JSON 字符串
    result_json = json.dumps(result, ensure_ascii=False, indent=4)
    print(result_json)
