from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.globals import ThemeType
import pandas as pd


def generate_grouped_bar_chart():
    # 读取 CSV 文件
    df = pd.read_csv(r"D:\Users\Lyx\Desktop\listings.csv")

    # 删除 room_type 为 Hotel room 的数据
    df = df[df['room_type']!= 'Hotel room']

    # 对 price 列进行初步清洗，去除非数字字符
    df['price'] = df['price'].str.replace(r'[^\d.]', '', regex=True)

    # 将清洗后的 price 列转换为数值类型
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # 处理可能产生的 NaN 值（由转换失败导致），这里简单地填充为 0，你可以根据实际情况调整
    df['price'] = df['price'].fillna(0)

    # 检查并处理无穷大值
    df['price'] = df['price'].replace([float('inf'), float('-inf')], 0)

    # 过滤掉 price 超过 800 的数据
    df = df[df['price'] <= 800]

    # 把 Todt Hill 社区的 Entire room/apt 房型的价格设置为 0
    df.loc[(df['neighbourhood_cleansed'] == 'Todt Hill') & (df['room_type'] == 'Entire room/apt'), 'price'] = 0

    # 打印设置价格为 0 后 Todt Hill 社区 Entire room/apt 房型的价格
    todt_hill_price_after_set = df.loc[(df['neighbourhood_cleansed'] == 'Todt Hill') & (df['room_type'] == 'Entire room/apt'), 'price']


    # 按社区和房型分组，计算均值和标准差（保留两位小数）
    grouped = df.groupby(['neighbourhood_cleansed', 'room_type'])['price'].agg(['mean','std']).reset_index()
    grouped['mean'] = grouped['mean'].round(2)
    grouped['std'] = grouped['std'].round(2)

    # 假设价格大于均值 + 3 倍标准差为异常值，将其修正为均值，直接在 grouped 数据上操作
    for index, row in grouped.iterrows():
        condition = (df['neighbourhood_cleansed'] == row['neighbourhood_cleansed']) & (
            df['room_type'] == row['room_type']) & (df['price'] > row['mean'] + 3 * row['std'])
        df.loc[condition, 'price'] = row['mean']

    # 提取需要的列并计算每个社区不同房型的价格中位数
    final_df = df[['neighbourhood_cleansed', 'room_type', 'price']]
    grouped_df = final_df.groupby(['neighbourhood_cleansed', 'room_type'])['price'].median().unstack()


    # 创建一个柱状图对象
    bar = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="1600px", height="800px"))
        .add_xaxis(grouped_df.index.tolist())
    )

    # 为每种房型添加数据
    for room_type in grouped_df.columns:
        bar.add_yaxis(room_type, grouped_df[room_type].tolist(), category_gap="0%")

    # 设置全局配置项
    bar.set_global_opts(
        title_opts=opts.TitleOpts(title="各社区不同房型的均价分布"),
        xaxis_opts=opts.AxisOpts(name="社区名称", axislabel_opts=opts.LabelOpts(rotate=45)),
        yaxis_opts=opts.AxisOpts(name="房屋均价（美元/月）", min_=0),
        legend_opts=opts.LegendOpts(is_show=True),
        toolbox_opts=opts.ToolboxOpts(is_show=True)
    )

    # 渲染图表到 HTML 文件
    bar.render(r"D:\\python-learn\\price_analysis.html")

# 调用函数生成图表
generate_grouped_bar_chart()