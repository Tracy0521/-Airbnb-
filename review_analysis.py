import pandas as pd
import folium
from sklearn.preprocessing import MinMaxScaler

# 步骤 1：数据准备
# 读取 CSV 文件
df = pd.read_csv(r"D:\Users\Lyx\Desktop\listings.csv")

# 提取核心字段
df = df[['neighbourhood_group_cleansed', 'latitude', 'longitude', 'price', 'review_scores_rating', 'number_of_reviews']]
df.columns = ['社区名', '纬度', '经度', '价格', '评分', '评价数']

# 转换价格列的数据类型，去除 $ 符号并转换为数值
df['价格'] = df['价格'].str.replace('$', '').str.replace(',', '').astype(float)

# 筛除空值和异常值
df = df.dropna()

# 保留评价数大于等于 5 条的社区
df = df[df['评价数'] >= 5]

# 步骤 2：指标计算
# 按社区分组，求平均价格和平均评分
community_stats = df.groupby('社区名').agg({'价格': 'mean', '评分': 'mean', '评价数': 'first'}).reset_index()

# 价格反向归一化（低价→高值）
scaler = MinMaxScaler()
community_stats['价格归一化'] = 1 - scaler.fit_transform(community_stats[['价格']])

# 评分正向归一化
community_stats['评分归一化'] = scaler.fit_transform(community_stats[['评分']])

# 计算综合指数
community_stats['综合指数'] = 0.5 * community_stats['价格归一化'] + 0.5 * community_stats['评分归一化']

# 合并经纬度信息
community_stats = pd.merge(community_stats, df[['社区名', '纬度', '经度']], on='社区名', how='left').drop_duplicates()

# 步骤 3：选工具与底图
# 创建地图对象
m = folium.Map(location=[df['纬度'].mean(), df['经度'].mean()], zoom_start=11, tiles='OpenStreetMap')

# 定义颜色映射函数
def price_color(price):
    if price <= 100:
        return 'crimson'
    elif 101 <= price <= 300:
        return 'lightcoral'
    else:
        return 'pink'

def rating_color(rating):
    if rating > 4.8:
        return 'darkorange'
    elif 4.3 <= rating <= 4.7:
        return 'orange'
    else:
        return 'palegoldenrod'

def composite_color(index):
    if index > 0.8:
        return 'darkviolet'
    elif 0.6 <= index <= 0.79:
        return 'purple'
    else:
        return 'plum'

# 步骤 4：颜色配置
# 添加价格维度的图层
price_layer = folium.FeatureGroup(name='价格维度')
for _, row in community_stats.iterrows():
    folium.CircleMarker(
        location=[row['纬度'], row['经度']],
        radius=5,
        popup=f"社区名: {row['社区名']}<br>均价: {row['价格']:.2f}<br>评分: {row['评分']:.2f}<br>综合指数: {row['综合指数']:.2f}<br>评价数: {row['评价数']}",
        color=price_color(row['价格']),
        fill=True,
        fill_color=price_color(row['价格']),
        fill_opacity=0.7
    ).add_to(price_layer)
m.add_child(price_layer)

# 添加评分维度的图层
rating_layer = folium.FeatureGroup(name='评分维度')
for _, row in community_stats.iterrows():
    folium.CircleMarker(
        location=[row['纬度'], row['经度']],
        radius=5,
        popup=f"社区名: {row['社区名']}<br>均价: {row['价格']:.2f}<br>评分: {row['评分']:.2f}<br>综合指数: {row['综合指数']:.2f}<br>评价数: {row['评价数']}",
        color=rating_color(row['评分']),
        fill=True,
        fill_color=rating_color(row['评分']),
        fill_opacity=0.7
    ).add_to(rating_layer)
m.add_child(rating_layer)

# 添加综合维度的图层
composite_layer = folium.FeatureGroup(name='综合维度')
for _, row in community_stats.iterrows():
    folium.CircleMarker(
        location=[row['纬度'], row['经度']],
        radius=5,
        popup=f"社区名: {row['社区名']}<br>均价: {row['价格']:.2f}<br>评分: {row['评分']:.2f}<br>综合指数: {row['综合指数']:.2f}<br>评价数: {row['评价数']}",
        color=composite_color(row['综合指数']),
        fill=True,
        fill_color=composite_color(row['综合指数']),
        fill_opacity=0.7
    ).add_to(composite_layer)
m.add_child(composite_layer)

# 步骤 5：加交互与标注
# 添加图层切换控件
folium.LayerControl().add_to(m)

# 添加图例
legend_html = '''
<div style="position: fixed; 
     bottom: 100px; right: 10px; width: 150px; height: 180px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white;
     ">&nbsp; 价格维度<br>
     &nbsp; 低价（≤100）：<i style="background:crimson;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br>
     &nbsp; 中价（101 - 300）：<i style="background:lightcoral;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br>
     &nbsp; 高价（301+）：<i style="background:pink;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br><br>
     &nbsp; 评分维度<br>
     &nbsp; 极高分（4.8+）：<i style="background:darkorange;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br>
     &nbsp; 高分（4.3 - 4.7）：<i style="background:orange;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br>
     &nbsp; 低分（≤3.5）：<i style="background:palegoldenrod;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br><br>
     &nbsp; 综合维度<br>
     &nbsp; 最优（0.8+）：<i style="background:darkviolet;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br>
     &nbsp; 优质（0.6 - 0.79）：<i style="background:purple;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br>
     &nbsp; 待优化（<0.4）：<i style="background:plum;opacity:0.7;">&nbsp;&nbsp;&nbsp;&nbsp;</i><br><br>
     &nbsp; 数据说明：评价数≥5 条
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# 步骤 6：校验优化（手动核对）
# 这里无法自动随机检查 3-5 个社区，需要手动查看地图进行确认

# 保存地图为 HTML 文件
m.save('D:\\python-learn\\review_analysis.html')