import os
import streamlit as st
from streamlit.components.v1 import html
import map_visualization as mv
from map_visualization import (
    load_cleaned_clustered_listings as load_data,
    filter_listings as filter_data,
    create_nyc_folium_heatmap  # 只导入热力图函数
)
from streamlit_folium import st_folium
import pandas as pd

# 页面设置
st.set_page_config(
    page_title="纽约市Airbnb数据分析系统",
    page_icon="🏨",
    layout="wide"
)

# 标题和介绍
st.title("🏨 纽约市Airbnb数据分析系统")
st.markdown("---")

# 侧边栏导航
st.sidebar.title("导航菜单")
page = st.sidebar.radio(
    "选择要查看的页面:",
    ["首页", "房源空间分布", "价格特征分析", "用户评价分析", "关于我们"]
)

# 首页内容
if page == "首页":
    st.header("欢迎使用纽约市Airbnb数据分析系统")
    st.markdown("""
    本系统基于纽约市Airbnb开放数据，提供以下功能:
    
    - **房源空间分布与社区特征**: 在地图上可视化房源分布，分析不同社区的特征
    - **价格特征分析**: 分析不同区域、房型的价格分布和趋势
    - **用户评价与口碑分析**: 探索用户评价数据，了解房源口碑情况
    
    ### 数据来源
    数据来自Inside Airbnb的纽约市开放数据集:
    [https://insideairbnb.com/get-the-data/](https://insideairbnb.com/get-the-data/)
    """)

    # 加载数据并显示真实统计
    try:
        with st.spinner('正在加载数据...'):
            df = load_data("清洗并聚类后的房源数据.xlsx")

        # 添加真实数据概览
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("数据概览")
            st.metric("总房源数", f"{len(df):,}")

            # 计算平均价格
            if 'price' in df.columns:
                avg_price = df['price'].mean()
                st.metric("平均价格", f"${avg_price:.2f}")
            else:
                st.metric("平均价格", "N/A")

            # 查找评分列并计算平均评分
            rating_cols = ['review_scores_rating', 'rating', 'review_score']
            rating_col = next((col for col in rating_cols if col in df.columns), None)
            if rating_col:
                avg_rating = df[rating_col].mean()
                st.metric("平均评分", f"{avg_rating:.2f}/5")
            else:
                st.metric("平均评分", "N/A")

    except Exception as e:
        # 如果加载失败，显示占位数据
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("数据概览")
            st.metric("总房源数", "N/A")
            st.metric("平均价格", "N/A")
            st.metric("平均评分", "N/A")

    with col2:
        st.subheader("快速导航")
        st.info("使用左侧菜单导航到不同功能页面")

# 其他页面保持不变...

# 房源空间分布页面
# 房源空间分布页面
elif page == "房源空间分布":
    st.header("房源空间分布与社区特征")
    st.markdown("""
    本页面展示纽约市Airbnb房源的地理分布情况，包括:
    - 各行政区的房源密度
    - 不同房型的空间分布
    - 社区特征分析
    """)

    # 筛选选项
    st.subheader("数据筛选")
    col1, col2, col3, col4 = st.columns(4)

    # 先加载数据来获取可用的选项
    try:
        with st.spinner('正在加载数据...'):# 显示加载提示
            df = load_data("清洗并聚类后的房源数据.xlsx")# 调用数据加载函数
        st.success('数据加载成功!')

        # 获取可用的选项 - 修改部分开始
        available_neighborhoods = ["全部"]

        # 检查多个可能的列名，与 map_visualization.py 保持一致
        neighborhood_col = None
        for col in ['neighborhood', 'neighbourhood', 'neighbourhood_cleansed']:
            if col in df.columns:
                neighborhood_col = col
                break

        if neighborhood_col:
            available_neighborhoods.extend(sorted(df[neighborhood_col].dropna().unique().tolist()))
            st.sidebar.info(f"使用社区列: {neighborhood_col}")  # 可选：显示使用的列名
        else:
            st.sidebar.warning("未找到社区相关的列")
        # 修改部分结束

        available_room_types = ["全部"]
        if 'room_type' in df.columns:
            available_room_types.extend(sorted(df['room_type'].dropna().unique().tolist()))

        available_cluster_types = ["全部"]
        if 'cluster_type' in df.columns:
            available_cluster_types.extend(sorted(df['cluster_type'].dropna().unique().tolist()))

        with col1:# 在第一列添加社区选择下拉框
            neighborhood = st.selectbox("选择社区", available_neighborhoods)
        with col2:
            room_type = st.selectbox("选择房型", available_room_types)
        with col3:
            cluster_type = st.selectbox("聚类类别", available_cluster_types)
        with col4:
            max_price = int(df['price'].max()) if 'price' in df.columns else 1000
            price_range = st.slider("价格范围", 0, max_price, (50, min(300, max_price)))

        # 显示筛选结果
        st.write(f"已选择: {neighborhood}, {room_type}, 价格${price_range[0]}-${price_range[1]}, 聚类: {cluster_type}")

        # 调用筛选函数，根据选择条件过滤数据
        filtered_df = filter_data(
            df,
            neighborhood=neighborhood if neighborhood != "全部" else "全部",# 如果选择"全部"则传递"全部"
            room_type=room_type if room_type != "全部" else "全部",
            price_range=price_range,
            cluster_type=cluster_type if cluster_type != "全部" else "全部",
        )

        st.success(f"找到 {len(filtered_df)} 个符合条件的房源")

        # 生成并显示folium热力图
        st.subheader("房源分布热力图")
        if len(filtered_df) > 0:
            heatmap = create_nyc_folium_heatmap(filtered_df, title="纽约房源热力图")
            # 使用st_folium显示地图，设置合适的宽度和高度
            map_data = st_folium(
                heatmap,
                width=1200,
                height=600,
                key="heatmap"
            )

            # 添加地图交互信息
            if map_data and map_data.get('last_clicked'):
                st.write(f"最后点击位置: {map_data['last_clicked']}")
        else:
            st.warning("没有找到符合条件的房源数据，无法生成热力图")

        # 显示数据表格 - 检查列是否存在
        st.subheader("筛选结果数据")
        display_columns = []
        # 修改部分开始：使用确定的列名
        if neighborhood_col:
            display_columns.append(neighborhood_col)
        # 修改部分结束

        for col in ['name', 'room_type', 'price', 'review_scores_rating']:
            if col in filtered_df.columns:
                display_columns.append(col)

        if display_columns and len(filtered_df) > 0:
            # 使用st.dataframe替代st.table，并设置高度和滚动
            st.dataframe(
                filtered_df[display_columns],
                height=400,  # 设置固定高度
                use_container_width=True
            )

            # 添加下载按钮
            csv = filtered_df[display_columns].to_csv(index=False)
            st.download_button(
                label="下载筛选数据 (CSV)",
                data=csv,
                file_name="filtered_airbnb_listings.csv",
                mime="text/csv",
            )
        else:
            st.warning("没有可显示的数据")

    except Exception as e:
        st.error(f"数据加载或处理出错: {str(e)}")
        st.info("请确保数据文件存在且格式正确")
        # 显示详细的错误信息
        import traceback
        st.code(traceback.format_exc())

# 价格特征分析页面
elif page == "价格特征分析":
    st.header("价格特征分析")
    st.markdown("""
    本页面分析纽约市Airbnb房源的价格特征，包括:
    - 不同区域的价格对比
    - 不同房型的价格分布
    """)

    # 直接显示预先生成的图表文件
    chart_path = "price_analysis.html"

    if os.path.exists(chart_path):
        try:
            # 读取HTML文件内容
            with open(chart_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 使用iframe显示图表
            st.subheader("各社区不同房型的均价分布")

            # 设置合适的宽度和高度
            st.components.v1.html(html_content, height=850, width="90%",scrolling=True)

            # 添加一些说明
            st.markdown("""
            **图表说明：**
            - 该图表展示了纽约市各社区不同房型（整套房子/公寓、独立房间、共享房间）的平均价格分布
            - 您可以使用图表右上角的工具栏进行缩放、保存图片等操作
            - 将鼠标悬停在柱状图上可以查看具体数值
            """)

        except Exception as e:
            st.error(f"读取图表文件时出错: {str(e)}")
    else:
        st.warning("价格分析图表文件不存在")
        st.info("请确保 price_analysis.html 文件存在于 D:\\python-learn\\ 目录下")

# 用户评价分析页面
# 用户评价分析页面
elif page == "用户评价分析":
    st.header("用户评价与口碑分析")
    st.markdown("""
    本页面分析用户对Airbnb房源的评价，包括:
    - 评分分布情况
    - 口碑与价格的关系
    """)

    # 显示用户评价分析图表
    review_chart_path = "review_analysis.html"

    if os.path.exists(review_chart_path):
        try:
            # 读取HTML文件内容
            with open(review_chart_path, 'r', encoding='utf-8') as f:
                review_html_content = f.read()

            # 使用iframe显示图表
            st.subheader("用户评价分析图表")

            # 设置合适的宽度和高度
            st.components.v1.html(review_html_content, height=850, scrolling=True)

            # 添加图表说明
            st.markdown("""
            **图表说明：**
            - 该图表展示了用户评价的关键分析结果
            - 您可以使用图表右上角的工具栏进行交互操作
            """)

        except Exception as e:
            st.error(f"读取评价分析图表文件时出错: {str(e)}")
    else:
        st.warning("评价分析图表文件不存在")
        st.info("请确保 review_analysis.html 文件存在于当前目录下")



# 关于我们页面
elif page == "关于我们":
    st.header("关于我们")
    st.markdown("""
    ### 项目介绍
    本项目是纽约市Airbnb开放数据的分析与可视化系统，旨在提供深入的数据洞察和决策支持。
    
    ### 功能特点
    - 房源空间分布可视化
    - 价格特征分析
    - 用户评价分析
    - 价格预测模型
    
    ### 技术栈
    - 前端: Streamlit,Folium
    - 数据处理: Pandas
    - 机器学习: Scikit-learn, 
    - 数据可视化: pyecharts
    
    """)

    st.info("最后数据更新: 2023年10月")
    st.info("系统版本: v1.0")

