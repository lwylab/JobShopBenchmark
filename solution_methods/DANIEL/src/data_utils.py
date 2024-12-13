import os
import random
import re
import sys
import time

import numpy as np
from .common_utils import strToSuffix


def SD2_instance_generator(config):
    """
    :param config: a package of parameters
    :return: a fjsp instance generated by SD2, with
        job_length : the number of operations in each job (shape [J])
        op_pt: the processing time matrix with shape [N, M],
                where op_pt[i,j] is the processing time of the ith operation
                on the jth machine or 0 if $O_i$ can not process on $M_j$
        op_per_mch : the average number of compatible machines of each operation
    """
    n_j = config["env"]["n_j"]
    n_m = config["env"]["n_m"]
    if config["SD2_data_generation"]["op_per_job"] == 0:
        op_per_job = n_m
    else:
        op_per_job = config["SD2_data_generation"]["op_per_job"]

    low = config["env"]["low"]
    high = config["env"]["high"]
    data_suffix = config["data"]["suffix"]

    op_per_mch_min = 1
    if data_suffix == "nf":
        op_per_mch_max = 1
    elif data_suffix == "mix":
        op_per_mch_max = n_m
    else:
        op_per_mch_min = config["SD2_data_generation"]["op_per_mch_min"]
        op_per_mch_max = config["SD2_data_generation"]["op_per_mch_max"]
    if op_per_mch_min < 1 or op_per_mch_max > n_m:
        print(
            f"Error from Instance Generation: [{op_per_mch_min},{op_per_mch_max}] "
            f"with num_mch : {n_m}"
        )
        sys.exit()

    n_op = int(n_j * op_per_job)
    job_length = np.full(shape=(n_j,), fill_value=op_per_job, dtype=int)
    op_use_mch = np.random.randint(
        low=op_per_mch_min, high=op_per_mch_max + 1, size=n_op
    )

    op_per_mch = np.mean(op_use_mch)
    op_pt = np.random.randint(low=low, high=high + 1, size=(n_op, n_m))

    for row in range(op_pt.shape[0]):
        mch_num = int(op_use_mch[row])
        if mch_num < n_m:
            inf_pos = np.random.choice(np.arange(0, n_m), n_m - mch_num, replace=False)
            op_pt[row][inf_pos] = 0

    return job_length, op_pt, op_per_mch


def matrix_to_text(job_length, op_pt, op_per_mch):
    """
        Convert matrix form of the data into test form
    :param job_length: the number of operations in each job (shape [J])
    :param op_pt: the processing time matrix with shape [N, M],
                where op_pt[i,j] is the processing time of the ith operation
                on the jth machine or 0 if $O_i$ can not process on $M_j$
    :param op_per_mch: the average number of compatible machines of each operation
    :return: the standard text form of the instance
    """
    n_j = job_length.shape[0]
    n_op, n_m = op_pt.shape
    text = [f"{n_j}\t{n_m}\t{op_per_mch}"]

    op_idx = 0
    for j in range(n_j):
        line = f"{job_length[j]}"
        for _ in range(job_length[j]):
            use_mch = np.where(op_pt[op_idx] != 0)[0]
            line = line + " " + str(use_mch.shape[0])
            for k in use_mch:
                line = line + " " + str(k + 1) + " " + str(op_pt[op_idx][k])
            op_idx += 1

        text.append(line)

    return text


def text_to_matrix(text):
    """
            Convert text form of the data into matrix form
    :param text: the standard text form of the instance
    :return:  the matrix form of the instance
            job_length: the number of operations in each job (shape [J])
            op_pt: the processing time matrix with shape [N, M],
                where op_pt[i,j] is the processing time of the ith operation
                on the jth machine or 0 if $O_i$ can not process on $M_j$
    """
    n_j = int(re.findall(r"\d+\.?\d*", text[0])[0])
    n_m = int(re.findall(r"\d+\.?\d*", text[0])[1])

    job_length = np.zeros(n_j, dtype="int32")
    op_pt = []

    for i in range(n_j):
        content = np.array([int(s) for s in re.findall(r"\d+\.?\d*", text[i + 1])])
        job_length[i] = content[0]

        idx = 1
        for j in range(content[0]):
            op_pt_row = np.zeros(n_m, dtype="int32")
            mch_num = content[idx]
            next_idx = idx + 2 * mch_num + 1
            for k in range(mch_num):
                mch_idx = content[idx + 2 * k + 1]
                pt = content[idx + 2 * k + 2]
                op_pt_row[mch_idx - 1] = pt

            idx = next_idx
            op_pt.append(op_pt_row)

    op_pt = np.array(op_pt)

    return job_length, op_pt


def load_data_from_files(directory):
    """
        load all files within the specified directory
    :param directory: the directory of files
    :return: a list of data (matrix form) in the directory
    """
    if not os.path.exists(directory):
        return [], []

    dataset_job_length = []
    dataset_op_pt = []
    for root, dirs, files in os.walk(directory):
        # sort files by index
        files.sort(key=lambda s: int(re.findall(r"\d+", s)[0]))
        files.sort(key=lambda s: int(re.findall(r"\d+", s)[-1]))
        for f in files:
            # print(f)
            g = open(os.path.join(root, f), "r").readlines()
            job_length, op_pt = text_to_matrix(g)
            dataset_job_length.append(job_length)
            dataset_op_pt.append(op_pt)
    return dataset_job_length, dataset_op_pt


def pack_data_from_config(data_source, test_data):
    """
        load multiple data (specified by the variable 'test_data')
        of the specified data source.
    :param data_source: the source of data (SD1/SD2/BenchData)
    :param test_data: the list of data's name
    :return: a list of data (matrix form) and its name
    """
    data_list = []
    for data_name in test_data:
        data_path = f"./data/{data_source}/{data_name}"
        data_list.append((load_data_from_files(data_path), data_name))
    return data_list


def generate_data_to_files(seed, directory, config):
    """
        Generate data and save it to the specified directory
    :param seed: seed for data generation
    :param directory: the directory for saving files
    :param config: other parameters related to data generation
    """
    n_j = config.n_j
    n_m = config.n_m
    source = config.data_source
    batch_size = config.data_size
    data_suffix = config.data_suffix

    suffix = strToSuffix(data_suffix)
    low = config.low
    high = config.high

    filename = "{}x{}{}".format(n_j, n_m, suffix)
    np.random.seed(seed)
    random.seed(seed)

    print("-" * 25 + "Data Setting" + "-" * 25)
    print(f"seed : {seed}")
    print(f"data size : {batch_size}")
    print(f"data source: {source}")
    print(f"filename : {filename}")
    print(f"processing time : [{low},{high}]")
    print(f"mode : {data_suffix}")
    print("-" * 50)

    path = directory + filename

    if (not os.path.exists(path)) or config.cover_data_flag:
        if not os.path.exists(path):
            os.makedirs(path)

        for idx in range(batch_size):
            if source == "SD2":
                job_length, op_pt, op_per_mch = SD2_instance_generator(config=config)

                lines_doc = matrix_to_text(job_length, op_pt, op_per_mch)

                doc = open(
                    path
                    + "/"
                    + filename
                    + "_{}.fjs".format(str.zfill(str(idx + 1), 3)),
                    "w",
                )
                for i in range(len(lines_doc)):
                    print(lines_doc[i], file=doc)
                doc.close()
    else:
        print("the data already exists...")


class CaseGenerator:
    """
    the generator of SD1 data (imported from "songwenas12/fjsp-drl"),
    used for generating training instances

    Remark: the validation and testing intances of SD1 data are
    imported from "songwenas12/fjsp-drl"
    """

    def __init__(
        self,
        job_init,
        num_mas,
        opes_per_job_min,
        opes_per_job_max,
        nums_ope=None,
        path="./  ",
        flag_same_opes=True,
        flag_doc=False,
    ):
        # n_i
        self.str_time = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
        if nums_ope is None:
            nums_ope = []
        self.flag_doc = flag_doc  # Whether save the instance to a file
        self.flag_same_opes = flag_same_opes
        self.nums_ope = nums_ope
        self.path = path  # Instance save path (relative path)
        self.job_init = job_init
        self.num_mas = num_mas

        self.mas_per_ope_min = (
            1  # The minimum number of machines that can process an operation
        )
        self.mas_per_ope_max = num_mas

        self.opes_per_job_min = (
            opes_per_job_min  # The minimum number of operations for a job
        )
        self.opes_per_job_max = opes_per_job_max

        self.proctime_per_ope_min = 1  # Minimum average processing time
        self.proctime_per_ope_max = 20

        self.proctime_dev = 0.2

    def get_case(self, idx=0):
        """
        Generate FJSP instance
        :param idx: The instance number
        """
        self.num_jobs = self.job_init
        if not self.flag_same_opes:
            self.nums_ope = [
                random.randint(self.opes_per_job_min, self.opes_per_job_max)
                for _ in range(self.num_jobs)
            ]
        self.num_opes = sum(self.nums_ope)
        self.nums_option = [
            random.randint(self.mas_per_ope_min, self.mas_per_ope_max)
            for _ in range(self.num_opes)
        ]
        self.num_options = sum(self.nums_option)

        self.ope_ma = []
        for val in self.nums_option:
            self.ope_ma = self.ope_ma + sorted(
                random.sample(range(1, self.num_mas + 1), val)
            )
        self.proc_time = []

        self.proc_times_mean = [
            random.randint(self.proctime_per_ope_min, self.proctime_per_ope_max)
            for _ in range(self.num_opes)
        ]
        for i in range(len(self.nums_option)):
            low_bound = max(
                self.proctime_per_ope_min,
                round(self.proc_times_mean[i] * (1 - self.proctime_dev)),
            )
            high_bound = min(
                self.proctime_per_ope_max,
                round(self.proc_times_mean[i] * (1 + self.proctime_dev)),
            )
            proc_time_ope = [
                random.randint(low_bound, high_bound)
                for _ in range(self.nums_option[i])
            ]
            self.proc_time = self.proc_time + proc_time_ope

        self.num_ope_biass = [sum(self.nums_ope[0:i]) for i in range(self.num_jobs)]
        self.num_ma_biass = [sum(self.nums_option[0:i]) for i in range(self.num_opes)]
        line0 = "{0}\t{1}\t{2}\n".format(
            self.num_jobs, self.num_mas, self.num_options / self.num_opes
        )
        lines_doc = []
        lines_doc.append(
            "{0}\t{1}\t{2}".format(
                self.num_jobs, self.num_mas, self.num_options / self.num_opes
            )
        )
        for i in range(self.num_jobs):
            flag = 0
            flag_time = 0
            flag_new_ope = 1
            idx_ope = -1
            idx_ma = 0
            line = []
            option_max = sum(
                self.nums_option[
                    self.num_ope_biass[i] : (self.num_ope_biass[i] + self.nums_ope[i])
                ]
            )
            idx_option = 0
            while True:
                if flag == 0:
                    line.append(self.nums_ope[i])
                    flag += 1
                elif flag == flag_new_ope:
                    idx_ope += 1
                    idx_ma = 0
                    flag_new_ope += (
                        self.nums_option[self.num_ope_biass[i] + idx_ope] * 2 + 1
                    )
                    line.append(self.nums_option[self.num_ope_biass[i] + idx_ope])
                    flag += 1
                elif flag_time == 0:
                    line.append(
                        self.ope_ma[
                            self.num_ma_biass[self.num_ope_biass[i] + idx_ope] + idx_ma
                        ]
                    )
                    flag += 1
                    flag_time = 1
                else:
                    line.append(
                        self.proc_time[
                            self.num_ma_biass[self.num_ope_biass[i] + idx_ope] + idx_ma
                        ]
                    )
                    flag += 1
                    flag_time = 0
                    idx_option += 1
                    idx_ma += 1
                if idx_option == option_max:
                    str_line = " ".join([str(val) for val in line])
                    lines_doc.append(str_line)
                    break
        job_length, op_pt = text_to_matrix(lines_doc)
        if self.flag_doc:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            # doc = open(
            #     self.path + '/' + '{0}x{1}_{2}.fjs'.format(self.num_jobs, self.num_mas, str.zfill(str(idx + 1), 3)),
            #     'w')
            doc = open(self.path + f"/{self.str_time}.txt", "a")
            # doc = open(self.path + f'/ours.txt', 'a')
            for i in range(len(lines_doc)):
                print(lines_doc[i], file=doc)
            doc.close()

        return job_length, op_pt, self.num_options / self.num_opes