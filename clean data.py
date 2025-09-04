import pandas as pd
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ----------------------
# 1. 读取数据
# ----------------------
# 替换为你的Excel文件路径
# 相对路径写法（数据文件与脚本在同一文件夹下）
file_path = "listings.xlsx"
excel_file = pd.ExcelFile(file_path)

# 获取工作表名称（假设主要数据在'listings'表中）
sheet_names = excel_file.sheet_names
print(f"发现的工作表: {sheet_names}")

# 读取数据到DataFrame
df = excel_file.parse('listings')  # 如果工作表名称不同，请修改此处
print(f"原始数据形状: {df.shape}")

# ----------------------
# 2. 数据清洗
# ----------------------
# 2.1 删除没有价格的行
df_clean = df.dropna(subset=['price']).copy()
print(f"删除无价格数据后形状: {df_clean.shape}")

# 2.2 删除包含网址的行
# 定义网址匹配正则表达式
url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

# 遍历所有字符串类型的列，检查并删除包含网址的行
for col in df_clean.select_dtypes(include='object').columns:
    # 对每个单元格检查是否包含网址
    has_url = df_clean[col].apply(lambda x: isinstance(x, str) and bool(url_pattern.search(x)))
    df_clean = df_clean[~has_url]
print(f"删除含网址数据后形状: {df_clean.shape}")

# ----------------------
# 3. 房源聚类
# ----------------------
# 3.1 选择用于聚类的特征（价格、评分、可容纳人数）
features = ['price', 'review_scores_rating', 'accommodates']
cluster_data = df_clean[features].copy()

# 3.2 处理聚类特征中的缺失值
cluster_data = cluster_data.dropna()
print(f"处理聚类特征缺失值后形状: {cluster_data.shape}")

# 3.3 数据标准化（使各特征权重一致）
scaler = StandardScaler()
scaled_features = scaler.fit_transform(cluster_data)

# 3.4 使用KMeans进行聚类（分为3类：经济型、中档型、高档型）
kmeans = KMeans(n_clusters=3, random_state=42)  # random_state确保结果可复现
cluster_data['cluster_label'] = kmeans.fit_predict(scaled_features)

# 3.5 根据聚类中心给类别命名（根据价格等特征判断）
# 计算每个聚类的中心值，帮助确定类别名称
cluster_centers = pd.DataFrame(
    scaler.inverse_transform(kmeans.cluster_centers_),
    columns=features
)
print("\n聚类中心值:")
print(cluster_centers)

# 根据聚类中心的价格高低排序并命名
sorted_labels = cluster_centers.sort_values('price').index
cluster_names = {
    sorted_labels[0]: '经济型',
    sorted_labels[1]: '中档型',
    sorted_labels[2]: '高档型'
}
cluster_data['cluster_type'] = cluster_data['cluster_label'].map(cluster_names)

# ----------------------
# 4. 合并结果并保存
# ----------------------
# 将聚类结果合并回清洗后的数据集
df_result = df_clean.merge(
    cluster_data[['cluster_label', 'cluster_type']],
    left_index=True,
    right_index=True,
    how='left'
)

# 保存结果到新的Excel文件
output_path = "清洗并聚类后的房源数据.xlsx"  # 输出文件路径
df_result.to_excel(output_path, index=False)
print(f"\n处理完成！结果已保存至: {output_path}")