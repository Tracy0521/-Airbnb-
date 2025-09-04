import os
import pandas as pd
from typing import Optional, Tuple, Dict, Iterable
import folium
from folium.plugins import HeatMap

# 默认数据源：清洗并聚类后的房源数据.xlsx（与本文件同目录）
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "清洗并聚类后的房源数据.xlsx")

# 在map_visualization.py中添加以下代码
import requests  # 需要导入requests库用于from folium import GeoJson  # 导入GeoJson组件

def create_nyc_folium_heatmap(
        df: pd.DataFrame,
        title: str = "纽约房源热力图"
) -> folium.Map:
    """
    使用 Folium 创建纽约房源热力图，包含行政边界
    """
    # 创建纽约地图
    nyc_map = folium.Map(
        location=[40.7128, -74.0060],  # 纽约中心坐标 [纬度, 经度]
        zoom_start=11,
        tiles='OpenStreetMap',  # 使用 OpenStreetMap 底图
        width='100%',
        height='100%'
    )

    # 添加纽约行政边界（使用公开的GeoJSON数据源）
    try:
        # 纽约市行政区边界GeoJSON数据
        nyc_geojson_url = "https://data.cityofnewyork.us/api/geospatial/tqmj-j8zm?method=export&format=GeoJSON"
        response = requests.get(nyc_geojson_url)
        nyc_geojson = response.json()

        # 添加边界到地图，使用黑色线条
        GeoJson(
            nyc_geojson,
            style_function=lambda x: {
                'color': 'black',  # 边界线颜色
                'weight': 2,       # 线宽
                'fillOpacity': 0   # 填充透明度（0表示不填充）
            }
        ).add_to(nyc_map)
    except Exception as e:
        print(f"添加行政边界时出错: {e}")
        # 即使边界加载失败，也继续创建地图

    # 准备热力图数据（保持原有逻辑）
    heat_data = []
    for _, row in df.iterrows():
        if (pd.notna(row.get('latitude')) and
                pd.notna(row.get('longitude')) and
                isinstance(row.get('latitude'), (int, float)) and
                isinstance(row.get('longitude'), (int, float))):

            lat = float(row['latitude'])
            lng = float(row['longitude'])
            # 确保坐标在合理范围内（纽约大致范围）
            if 40.4 <= lat <= 41.0 and -74.5 <= lng <= -73.5:
                heat_data.append([lat, lng, 1])

    # 添加热力图（保持原有逻辑）
    if heat_data:
        HeatMap(
            heat_data,
            radius=15,      # 热力点半径
            blur=10,        # 模糊度
            max_zoom=15,    # 最大缩放级别
            gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}  # 颜色渐变
        ).add_to(nyc_map)
    else:
        print("警告：没有有效的热力图数据")

    # 添加标题（保持原有逻辑）
    title_html = f'''
             <h3 align="center" style="font-size:20px"><b>{title}</b></h3>
             '''
    nyc_map.get_root().html.add_child(folium.Element(title_html))

    return nyc_map


def load_cleaned_clustered_listings(path: Optional[str] = None) -> pd.DataFrame:
    """
    读取清洗并聚类后的房源数据 Excel 文件，直接使用已有字段不做额外处理。
    """
    data_path = path or DEFAULT_DATA_PATH
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"未找到数据文件: {data_path}")

    # 直接读取Excel文件
    df = pd.read_excel(data_path)

    # 仅进行基本的列名空格清理（避免后续访问问题）
    df.columns = [str(col).strip() for col in df.columns]

    # 确认必要字段存在，如果不存在则创建空列避免前端错误
    required_columns = ['price', 'latitude', 'longitude']
    for col in required_columns:
        if col not in df.columns:
            df[col] = pd.NA if col in ['latitude', 'longitude'] else 0

    # 确保数值列类型正确（简单转换，不进行过滤）
    for col in ["price", "latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def filter_listings(
        df: pd.DataFrame,
        neighborhood: str = "全部",
        room_type: str = "全部",
        price_range: Tuple[float, float] = (0, 10_000),
        cluster_type: str = "全部",
        valid_neighborhoods: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    按地区、房型、价格区间、聚类类别过滤房源数据。
    """
    filtered = df.copy()

    if neighborhood and neighborhood != "全部" and "neighborhood" in filtered.columns:
        if valid_neighborhoods:
            if neighborhood in set(valid_neighborhoods):
                filtered = filtered[filtered["neighborhood"] == neighborhood]
        else:
            filtered = filtered[filtered["neighborhood"] == neighborhood]

    if room_type and room_type != "全部" and "room_type" in filtered.columns:
        filtered = filtered[filtered["room_type"] == room_type]

    if price_range is not None:
        low, high = price_range
        filtered = filtered[(filtered["price"] >= low) & (filtered["price"] <= high)]

    if cluster_type and cluster_type != "全部" and "cluster_type" in filtered.columns:
        filtered = filtered[filtered["cluster_type"] == cluster_type]

    # 严格要求经纬度存在
    filtered = filtered.dropna(subset=["latitude", "longitude"]).copy()
    return filtered