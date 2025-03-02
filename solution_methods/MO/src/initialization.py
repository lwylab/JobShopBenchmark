import logging
import multiprocessing

import numpy as np
from deap import base, creator, tools

from solution_methods.MO.src.operators import (
    evaluate_individual, evaluate_population, init_individual, mutate_sequence_exchange, mutate_shortest_proc_time,
    pox_crossover)
from solution_methods.helper_functions import set_seeds


def initialize_run(jobShopEnv, **kwargs):
    """
    初始化遗传算法运行环境，包括DEAP工具箱、统计信息和初始种群。
    """
    set_seeds(kwargs["algorithm"].get("seed", None))

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO)

    # 定义适应度和个体
    if not hasattr(creator, "FitnessMulti"):
        creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMulti)

    toolbox = base.Toolbox()

    if kwargs['algorithm']['multiprocessing']:
        pool = multiprocessing.Pool()
        toolbox.register("map", pool.map)

    # 注册基本操作
    toolbox.register("init_individual", init_individual, creator.Individual, jobShopEnv=jobShopEnv)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.init_individual)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate_individual, jobShopEnv=jobShopEnv)


    # 注册遗传操作
    toolbox.register("mate_TwoPoint", tools.cxTwoPoint)  # 添加两点交叉
    toolbox.register("mate_Uniform", tools.cxUniform, indpb=0.5)  # 添加均匀交叉
    toolbox.register("mate_POX", pox_crossover, nr_preserving_jobs=1)
    toolbox.register("mutate_machine_selection", mutate_shortest_proc_time, jobShopEnv=jobShopEnv)
    toolbox.register("mutate_operation_sequence", mutate_sequence_exchange)

    # 使用 NSGA-II 的选择操作
    toolbox.register("select", tools.selNSGA2)

    # 注册评估函数
    toolbox.register("evaluate_individual", evaluate_individual, jobShopEnv=jobShopEnv)

    # 设置统计信息跟踪
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    # 使用 ParetoFront 存储非支配解集
    pareto_front = tools.ParetoFront()

    try:
        # 初始化种群
        pop_size = kwargs['algorithm']['population_size']
        initial_population = toolbox.population(n=pop_size)

        # 评估初始种群
        fitnesses = evaluate_population(toolbox, initial_population)

        # 分配适应度值
        for ind, fit in zip(initial_population, fitnesses):
            ind.fitness.values = fit

        # 计算初始种群的非支配排序
        tools.emo.assignCrowdingDist(initial_population)

    except Exception as e:
        logging.error(f"在初始种群评估期间发生错误: {e}")
        return None, None, None, None

    return initial_population, toolbox, stats, pareto_front
