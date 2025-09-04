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

        # 获取可用的选项
        available_neighborhoods = ["全部"] # 默认包含"全部"选项
        if 'neighborhood' in df.columns:
            available_neighborhoods.extend(sorted(df['neighborhood'].dropna().unique().tolist()))# 去重、去空、排序后添加到选项列表

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
        for col in ['name', 'neighbourhood', 'neighborhood', 'room_type', 'price', 'review_scores_rating']:
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
    - 价格随时间的变化趋势
    """)

    # 占位图表
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("各区域平均价格")
        st.info("此处将显示柱状图，比较各区域的平均价格")

    with col2:
        st.subheader("价格分布")
        st.info("此处将显示箱线图，展示价格分布情况")

    # 价格趋势
    st.subheader("价格趋势分析")
    st.info("此处将显示折线图，展示价格随时间的变化趋势")

# 用户评价分析页面
elif page == "用户评价分析":
    st.header("用户评价与口碑分析")
    st.markdown("""
    本页面分析用户对Airbnb房源的评价，包括:
    - 评分分布情况
    - 评价关键词分析
    - 口碑与价格的关系
    """)

    # 占位内容
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("评分分布")
        st.info("此处将显示 histogram，展示评分分布")

    with col2:
        st.subheader("评价词云")
        st.info("此处将显示词云图，展示高频评价词汇")

    # 情感分析
    st.subheader("情感分析")
    st.info("此处将显示情感分析结果，展示正面/负面评价比例")

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
    - 前端: Streamlit, Plotly, Folium
    - 数据处理: Pandas, NumPy
    - 机器学习: Scikit-learn, XGBoost
    - 数据可视化: Matplotlib, Seaborn
    
    ### 开发团队
    - 数据科学家: [您的名字]
    - 开发工程师: [团队成员]
    - UI/UX设计师: [团队成员]
    """)

    st.info("最后数据更新: 2023年10月")
    st.info("系统版本: v1.0")

# 运行说明
st.sidebar.markdown("---")
st.sidebar.info("""
### 运行说明
1. 确保已安装所需依赖
2. 在终端运行: `streamlit run airbnb_app.py`
3. 在浏览器中打开显示的本地地址
""")