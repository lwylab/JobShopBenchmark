import matplotlib.colors as mcolors



def create_colormap():
    # Create a custom colormap to prevent repeating colors
    # colors = [
    #     '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c',
    #     '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
    #     '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
    #     '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5',
    #     '#393b79', '#637939', '#8c6d31', '#843c39', '#5254a3',
    #     '#6b4c9a', '#8ca252', '#bd9e39', '#ad494a', '#636363',
    #     '#8c6d8c', '#9c9ede', '#cedb9c', '#e7ba52', '#e7cb94',
    #     '#843c39', '#ad494a', '#d6616b', '#e7969c', '#7b4173',
    #     '#a55194', '#ce6dbd', '#de9ed6', '#f1b6da', '#fde0ef',
    #     '#636363', '#969696', '#bdbdbd', '#d9d9d9', '#f0f0f0',
    #     '#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#e6550d',
    #     '#fd8d3c', '#fdae6b', '#fdd0a2', '#31a354', '#74c476',
    #     '#a1d99b', '#c7e9c0', '#756bb1', '#9e9ac8', '#bcbddc',
    #     '#dadaeb', '#636363', '#969696', '#bdbdbd', '#d9d9d9',
    #     '#f0f0f0', '#a63603', '#e6550d', '#fd8d3c', '#fdae6b',
    #     '#fdd0a2', '#31a354', '#74c476', '#a1d99b', '#c7e9c0',
    #     '#756bb1', '#9e9ac8', '#bcbddc', '#dadaeb', '#636363',
    #     '#969696', '#bdbdbd', '#d9d9d9', '#f0f0f0', '#6a3d9a',
    #     '#8e7cc3', '#b5a0d8', '#ce6dbd', '#de9ed6', '#f1b6da',
    #     '#fde0ef', '#3182bd', '#6baed6', '#9ecae1', '#c6dbef'
    # ]

    # 学术期刊风格的颜色方案 - 饱和度低，更沉稳专业
    colors = [
        # 蓝色系列
        '#1f77b4', '#4c78a8', '#6395b9', '#9ecae1', '#c6dbef',
        # 红色系列
        '#d62728', '#e45756', '#f67e7d', '#fc9272', '#fee0d2',
        # 紫色系列
        '#9467bd', '#8c6bb1', '#9e9ac8', '#bcbddc', '#dadaeb',
        # 橙色系列
        '#ff7f0e', '#f58518', '#fd8d3c', '#fdae6b', '#fdd0a2',
        # 棕色系列
        '#8c564b', '#a05d56', '#bd6b63', '#d8856a', '#e5ae83',
        # 灰色系列
        '#7f7f7f', '#969696', '#bdbdbd', '#d9d9d9', '#f0f0f0',
        # 青色系列
        '#17becf', '#6dccda', '#a5e0e3', '#b7e6dc', '#d3f2df',
        # 绿色系列
        '#2ca02c', '#5cb85c', '#78c679', '#a1d99b', '#c7e9c0',
        # 其他辅助色
        '#3a4cc0', '#674ea7', '#8864b0', '#b14d57', '#c44e52',
        '#31a354', '#6c7c0e', '#507c36', '#7e4e90', '#995688',
        '#756bb1', '#636363', '#525252', '#6b6ecf', '#9c9ede'
    ]
    return mcolors.ListedColormap(colors)