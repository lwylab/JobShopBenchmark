import csv
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple

from solution_methods.dispatching_rules.run_dispatching_rules import run_dispatching_rules
from solution_methods.helper_functions import load_job_shop_env, load_parameters
from visualization import gantt_chart


def ensure_directory_exists(filepath: str) -> None:
    """确保目录存在，如果不存在则创建"""
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)


def run_single_instance(instance_path: str, parameters: Dict, result_dir: str) -> Tuple[str, float, float, List, int, int, int]:
    """运行单个实例的调度规则算法"""
    try:
        jobShopEnv = load_job_shop_env(instance_path)

        start_time = time.time()
        makespan, jobShopEnv = run_dispatching_rules(jobShopEnv, **parameters)
        computation_time = time.time() - start_time

        instance = re.split(r'[/.]', jobShopEnv.instance_name)
        title = instance[3] if len(instance) > 3 else "N/A"

        # 绘制甘特图并保存到结果目录
        gantt_chart.plot(jobShopEnv, save_dir=result_dir)

        # 收集操作调度信息
        result = []
        for op in jobShopEnv.operations:
            row = op.scheduling_information  # 这是一个dict
            row.update({'job_id': op.job_id, 'operation_id': op.operation_id})
            result.append(row)

        jobs = jobShopEnv.nr_of_jobs
        machines = jobShopEnv.nr_of_machines
        operations = jobShopEnv.nr_of_operations

        return title, makespan, computation_time, result, jobs, machines, operations
    except Exception as e:
        print(f"处理实例 {instance_path} 时发生错误: {str(e)}")
        return instance_path, -1, -1, [], -1, -1, -1


def save_results_to_csv(results: List[Dict], filename: str) -> None:
    """保存结果到CSV文件"""
    try:
        ensure_directory_exists(filename)
        fieldnames = ['Instance', 'Makespan', 'Computation Time', 'Jobs', 'Machines', 'Operations']
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n实验结果已成功保存至: {filename}")
    except Exception as e:
        print(f"保存CSV文件时发生错误: {str(e)}")
        raise  # 添加异常重抛，以便更好地追踪错误


def save_scheduling_info(scheduling_info: List, instance_name: str, result_dir: str) -> None:
    """保存调度信息到JSON文件"""
    try:
        filename = os.path.join(result_dir, f"{instance_name}_scheduling_info.json")
        ensure_directory_exists(filename)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scheduling_info, f, ensure_ascii=False, indent=4)
        print(f"调度信息已保存至: {filename}")
    except Exception as e:
        print(f"保存调度信息时发生错误: {str(e)}")


def main():
    try:
        # 加载参数配置
        parameters = load_parameters("configs/dispatching_rules.toml")
        if not parameters:
            raise ValueError("无法加载配置文件")

        # 创建实验结果列表和CSV文件名
        results = []
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = os.path.join("results", f"Dispatching_Rules_experiment_{current_time}")
        ensure_directory_exists(os.path.join(result_dir, "placeholder"))  # 确保目录存在
        csv_filename = os.path.join(result_dir, "Dispatching_Rules_results.csv")

        # 循环处理MFJS1到MFJS10
        for i in range(1, 11):
            problem_instance = f"/fjsp/fattahi/MFJS{i}.fjs"
            print(f"\n{'=' * 20}\n正在处理实例 MFJS{i}\n{'=' * 20}")

            title, makespan, computation_time, scheduling_info, jobs, machines, operations = run_single_instance(problem_instance, parameters, result_dir)

            results.append({
                'Instance': title,
                'Makespan': makespan,
                'Computation Time': computation_time,
                'Jobs': jobs,
                'Machines': machines,
                'Operations': operations
            })

            print(f"实例: {title}")
            print(f"最大完工时间: {makespan}")
            print(f"计算耗时: {computation_time:.2f}秒")
            print(f"作业数: {jobs}")
            print(f"机器数: {machines}")
            print(f"操作数: {operations}")

            # 保存调度信息
            if scheduling_info:
                save_scheduling_info(scheduling_info, title, result_dir)

        # 可选：测试brandimarte实例
        # brandimarte_instances = [f"/fjsp/brandimarte/Mk{i}.fjs" for i in range(1, 11)]
        # for instance_path in brandimarte_instances:
        #     instance_name = instance_path.split('/')[-1].split('.')[0]
        #     print(f"\n{'=' * 20}\n正在处理实例 {instance_name}\n{'=' * 20}")
        #
        #     title, makespan, computation_time, scheduling_info, jobs, machines, operations = run_single_instance(instance_path, parameters, result_dir)
        #
        #     results.append({
        #         'Instance': title,
        #         'Makespan': makespan,
        #         'Computation Time': computation_time,
        #         'Jobs': jobs,
        #         'Machines': machines,
        #         'Operations': operations
        #     })
        #
        #     print(f"实例: {title}")
        #     print(f"最大完工时间: {makespan}")
        #     print(f"计算耗时: {computation_time:.2f}秒")
        #     print(f"作业数: {jobs}")
        #     print(f"机器数: {machines}")
        #     print(f"操作数: {operations}")
        #     
        #     # 保存调度信息
        #     if scheduling_info:
        #         save_scheduling_info(scheduling_info, title, result_dir)

        # 保存实验结果
        save_results_to_csv(results, csv_filename)

    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")


if __name__ == '__main__':
    main()
