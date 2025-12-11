import streamlit as st
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import altair as alt  # 引入Altair实现高级图表（无参数冲突）

# ---------------------- 页面高级配置 ----------------------
st.set_page_config(
    page_title="上市公司数字化转型分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式（高级UI）
def add_custom_style():
    st.markdown("""
    <style>
    .card {background-color: #ffffff; border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);}
    .section-title {font-size: 1.6rem; font-weight: 700; color: #2d3748; margin-bottom: 16px; border-left: 4px solid #4299e1; padding-left: 12px;}
    .stDataFrame {border-radius: 12px; border: none; font-size: 0.9rem;}
    .css-1d391kg {padding-top: 2rem; background-color: #f8fafc;}
    .stButton > button {background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); color: white; border-radius: 8px; border: none; padding: 8px 16px;}
    </style>
    """, unsafe_allow_html=True)

def main():
    add_custom_style()

    # 侧边栏筛选
    with st.sidebar:
        st.header("🔍 数据筛选")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "总词频统计表.xlsx")
        try:
            df_temp = pd.read_excel(file_path)
            df_temp = df_temp.fillna(0)
            min_year = int(df_temp["年份"].min())
            max_year = int(df_temp["年份"].max())
        except Exception as e:
            st.error(f"❌ 读取失败：{str(e)}")
            return

        selected_years = st.slider("选择年份范围", min_year, max_year, (min_year, max_year), step=1)
        digital_dimensions = ["人工智能词频数", "大数据词频数", "云计算词频数", "区块链词频数", "数字技术运用词频数"]
        selected_dimensions = st.multiselect("选择技术维度", digital_dimensions, digital_dimensions)
        min_index = st.number_input("最小数字化指数", 0.0, 100.0, 0.0, step=5.0)
        st.divider()
        st.info(f"📌 数据概览：{selected_years[0]}-{selected_years[1]}年 | {len(df_temp)}家企业")

    # 读取并筛选数据
    try:
        df = pd.read_excel(file_path)
        df = df.fillna(0)
        df = df[(df["年份"] >= selected_years[0]) & (df["年份"] <= selected_years[1])]
        
        # 计算指数
        df_scaled = StandardScaler().fit_transform(df[digital_dimensions])
        pca = PCA(n_components=1)
        pca_result = pca.fit_transform(df_scaled)
        df["数字化转型指数"] = (pca_result - pca_result.min()) / (pca_result.max() - pca_result.min()) * 100
        df["数字化转型指数"] = df["数字化转型指数"].round(2)
        df = df[df["数字化转型指数"] >= min_index]

        st.success(f"✅ 数据加载完成！有效数据：{len(df)}条")
    except Exception as e:
        st.error(f"❌ 数据处理失败：{str(e)}")
        return

    # ---------------------- 功能1：企业查询 ----------------------
    st.divider()
    with st.container():
        st.markdown('<div class="card"><div class="section-title">🔍 企业精准查询</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2,2,1])
        with col1: stock_code = st.text_input("股票代码（模糊匹配）")
        with col2: company_name = st.text_input("企业名称（模糊匹配）")
        with col3: st.markdown("<br>", unsafe_allow_html=True); search_btn = st.button("执行查询")

        if search_btn or stock_code or company_name:
            query_result = df.copy()
            if stock_code: query_result = query_result[query_result["股票代码"].astype(str).str.contains(stock_code)]
            if company_name: query_result = query_result[query_result["企业名称"].str.contains(company_name)]
            
            if not query_result.empty:
                query_result = query_result.sort_values("数字化转型指数", ascending=False)
                st.dataframe(query_result[["股票代码", "企业名称", "年份", "数字化转型指数"]+selected_dimensions], hide_index=True)
                
                # 企业维度柱状图（Altair实现，高级美观）
                st.subheader("📈 企业维度词频分布")
                selected_company = st.selectbox("选择企业", query_result["企业名称"].unique())
                company_data = query_result[query_result["企业名称"] == selected_company].iloc[0]
                dim_df = pd.DataFrame({"技术维度": selected_dimensions, "词频数": [company_data[dim] for dim in selected_dimensions]})
                
                bar_chart = alt.Chart(dim_df).mark_bar(color="#4299e1").encode(
                    x=alt.X("技术维度:N", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("词频数:Q"),
                    tooltip=["技术维度", "词频数"]
                ).properties(height=350, width=700)
                st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.warning("⚠️ 未找到匹配企业")
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- 功能2：年度趋势（修复图表参数） ----------------------
    st.divider()
    with st.container():
        st.markdown('<div class="card"><div class="section-title">📅 年度数字化转型趋势</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        # 左栏：年度指数趋势（Altair实现，支持自定义颜色）
        with col1:
            st.subheader("年度平均转型指数")
            year_index_trend = df.groupby("年份")["数字化转型指数"].agg(["mean", "median", "max"]).round(2)
            year_index_trend.columns = ["指数均值", "指数中位数", "指数最大值"]
            trend_long = year_index_trend.reset_index().melt(id_vars="年份", var_name="指标", value_name="指数")
            
            # Altair线图（无参数冲突，颜色自定义）
            line_chart = alt.Chart(trend_long).mark_line().encode(
                x=alt.X("年份:O", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("指数:Q"),
                color=alt.Color("指标:N", scale=alt.Scale(range=["#4299e1", "#38b2ac", "#ed64a6"])),
                tooltip=["年份", "指标", "指数"]
            ).properties(height=350, width=500)
            st.altair_chart(line_chart, use_container_width=True)

        # 右栏：维度词频趋势
        with col2:
            st.subheader("年度维度词频均值")
            year_dim_trend = df.groupby("年份")[selected_dimensions].mean().round(2).reset_index().melt(id_vars="年份", var_name="维度", value_name="词频均值")
            dim_line_chart = alt.Chart(year_dim_trend).mark_line().encode(
                x="年份:O", y="词频均值:Q", color="维度:N", tooltip=["年份", "维度", "词频均值"]
            ).properties(height=350, width=500)
            st.altair_chart(dim_line_chart, use_container_width=True)

        # 年度统计表格
        st.subheader("年度数据统计")
        year_summary = df.groupby("年份").agg({
            "数字化转型指数": ["count", "mean", "median", "max", "min"],
            "人工智能词频数": "mean"
        }).round(2)
        year_summary.columns = ["企业数量", "指数均值", "指数中位数", "指数最大值", "指数最小值", "AI词频均值"]
        st.dataframe(year_summary, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- 功能3：TOP榜单 ----------------------
    st.divider()
    with st.container():
        st.markdown('<div class="card"><div class="section-title">🏆 数字化转型TOP榜单</div>', unsafe_allow_html=True)
        top_n = st.slider("选择TOP数量", 5, 30, 10, step=5)
        col1, col2 = st.columns(2)

        # 年度TOP
        with col1:
            st.subheader(f"年度TOP{top_n}")
            year_top = []
            for year in sorted(df["年份"].unique()):
                year_data = df[df["年份"] == year].sort_values("数字化转型指数", ascending=False).head(top_n)
                year_data["年份排名"] = range(1, len(year_data)+1)
                year_top.append(year_data)
            st.dataframe(pd.concat(year_top)[["年份", "年份排名", "企业名称", "数字化转型指数"]], hide_index=True)

        # 综合TOP
        with col2:
            st.subheader(f"综合TOP{top_n}")
            company_top = df.loc[df.groupby("企业名称")["数字化转型指数"].idxmax()].sort_values("数字化转型指数", ascending=False).head(top_n)
            company_top["综合排名"] = range(1, len(company_top)+1)
            st.dataframe(company_top[["综合排名", "企业名称", "年份", "数字化转型指数"]], hide_index=True)

        # TOP企业热力图（Altair实现）
        st.subheader(f"TOP{top_n}企业维度热力图")
        top_heatmap = company_top[["企业名称"]+selected_dimensions].set_index("企业名称").reset_index().melt(id_vars="企业名称", var_name="维度", value_name="词频")
        heatmap = alt.Chart(top_heatmap).mark_rect().encode(
            x=alt.X("企业名称:N", axis=alt.Axis(labelAngle=-45)),
            y="维度:N",
            color=alt.Color("词频:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["企业名称", "维度", "词频"]
        ).properties(width=700, height=300)
        st.altair_chart(heatmap, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()