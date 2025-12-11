import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# 页面基础配置
st.set_page_config(
    page_title="上市公司数字化转型分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS美化（更精致）
st.markdown("""
    <style>
    .main {background-color: #f5f7fa;}
    .sidebar .sidebar-content {background-color: #ffffff; color: #000000;} /* 侧边栏背景改为白色，字体黑色 */
    h1 {color: #1e3a8a; font-size: 2.8rem; font-weight: 800; text-align: center; margin-bottom: 1rem;}
    h2 {color: #3b82f6; font-size: 1.8rem; font-weight: 700; border-left: 4px solid #3b82f6; padding-left: 0.8rem;}
    h3 {color: #1e40af; font-size: 1.4rem; font-weight: 600; margin-top: 1.2rem;}
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 8px 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------
# 数据加载（确保全年份覆盖）
# --------------------------
@st.cache_data
def load_data():
    try:
        with st.spinner("正在加载1999-2023年完整数据..."):
            df = pd.read_excel(
                r"C:\Users\31030\Desktop\aaxx\上市公司数字化合并总表.xlsx",
                engine="openpyxl",
                dtype={"股票代码": str}
            )
            # 强制保留1999-2023所有年份（补全缺失年份的空数据，避免折线断裂）
            all_years = pd.DataFrame({'年份': list(range(1999, 2024))})  # 转成列表
            df = pd.merge(all_years, df, on='年份', how='left')
            # 补充行业列
            if "行业" not in df.columns:
                df["行业"] = "未分类"
            return df
    except Exception as e:
        st.error(f"数据加载失败：{str(e)}")
        st.stop()

# --------------------------
# 核心功能函数
# --------------------------
def get_company_full_data(df, query):
    """查询企业1999-2023所有年份数据"""
    query = str(query).strip()
    mask = (df['股票代码'].str.contains(query, na=False)) | (df['企业名称'].str.contains(query, na=False))
    company_data = df[mask].copy()
    # 强制补充1999-2023所有年份（确保折线图完整）
    company_data = pd.merge(pd.DataFrame({'年份': list(range(1999, 2024))}), company_data, on='年份', how='left')  # 转成列表
    # 填充企业名称/代码（避免空值）
    if not company_data['企业名称'].dropna().empty:
        company_data['企业名称'] = company_data['企业名称'].fillna(company_data['企业名称'].dropna().iloc[0])
        company_data['股票代码'] = company_data['股票代码'].fillna(company_data['股票代码'].dropna().iloc[0])
        company_data['行业'] = company_data['行业'].fillna(company_data['行业'].dropna().iloc[0])
    return company_data.sort_values('年份') if not company_data.empty else None

def plot_company_full_trend(company_data):
    """绘制企业1999-2023全年份折线图（含所有指标）"""
    company_name = company_data['企业名称'].iloc[0] if not company_data['企业名称'].isna().all() else "未知企业"
    stock_code = company_data['股票代码'].iloc[0] if not company_data['股票代码'].isna().all() else "未知代码"
    
    # 创建多指标子图
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("数字化转型指数趋势", "数字技术词频数趋势"),
        vertical_spacing=0.15
    )
    
    # 子图1：数字化转型指数
    fig.add_trace(
        go.Scatter(
            x=company_data['年份'],
            y=company_data['数字化转型指数'],
            name='转型指数',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=6, color='#3b82f6'),
            hovertemplate='年份: %{x}<br>指数: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 子图2：各技术词频数
    tech_cols = ['人工智能词频数', '大数据词频数', '云计算词频数', '区块链词频数']
    colors = ['#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
    for col, color in zip(tech_cols, colors):
        fig.add_trace(
            go.Scatter(
                x=company_data['年份'],
                y=company_data[col],
                name=col.replace('词频数', ''),
                line=dict(color=color, width=2),
                marker=dict(size=4),
                hovertemplate='年份: %{x}<br>词频数: %{y}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # 图表样式优化
    fig.update_layout(
        title=f"{company_name}（{stock_code}）1999-2023数字化转型全趋势",
        title_font=dict(size=18, weight='bold', color='#1e3a8a'),
        width=900,
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=20, r=20, t=80, b=80)
    )
    # 修正tickvals为列表
    fig.update_xaxes(
        title_text='年份',
        tickvals=list(range(1999, 2024, 2)),  # 关键：range转列表
        gridcolor='#e5e7eb',
        row=1, col=1
    )
    fig.update_xaxes(
        title_text='年份',
        tickvals=list(range(1999, 2024, 2)),  # 关键：range转列表
        gridcolor='#e5e7eb',
        row=2, col=1
    )
    fig.update_yaxes(title_text='转型指数', gridcolor='#e5e7eb', row=1, col=1)
    fig.update_yaxes(title_text='词频数', gridcolor='#e5e7eb', row=2, col=1)
    return fig

def plot_market_full_trend(df):
    """绘制全市场1999-2023完整年份折线图"""
    # 计算每年平均指数
    market_trend = df.groupby('年份')['数字化转型指数'].mean().reset_index()
    # 补全所有年份（确保折线连续）
    market_trend = pd.merge(pd.DataFrame({'年份': list(range(1999, 2024))}), market_trend, on='年份', how='left')  # 转列表
    
    fig = px.line(
        market_trend,
        x='年份',
        y='数字化转型指数',
        title='全市场1999-2023年数字化转型指数平均趋势',
        width=900,
        height=400,
        color_discrete_sequence=['#2563eb'],
        template='plotly_white'
    )
    # 样式优化（修正tickvals为列表）
    fig.update_layout(
        title_font=dict(size=16, weight='bold'),
        plot_bgcolor='white',
        xaxis=dict(
            title='年份',
            tickvals=list(range(1999, 2024, 2)),  # 关键：range转列表
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title='平均转型指数',
            gridcolor='#e5e7eb'
        ),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    # 添加趋势线（更直观）
    fig.add_trace(
        go.Scatter(
            x=market_trend['年份'],
            y=market_trend['数字化转型指数'].rolling(3).mean(),  # 3年移动平均
            name='3年移动平均',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            hovertemplate='年份: %{x}<br>平均指数: %{y:.2f}<extra></extra>'
        )
    )
    return fig

def plot_tech_comparison(df):
    """绘制全市场各技术词频数年度平均对比"""
    tech_trend = df.groupby('年份')[['人工智能词频数', '大数据词频数', '云计算词频数', '区块链词频数']].mean().reset_index()
    tech_trend = pd.merge(pd.DataFrame({'年份': list(range(1999, 2024))}), tech_trend, on='年份', how='left')  # 转列表
    
    fig = px.line(
        tech_trend,
        x='年份',
        y=['人工智能词频数', '大数据词频数', '云计算词频数', '区块链词频数'],
        title='1999-2023年数字技术词频数全市场平均趋势',
        width=900,
        height=400,
        color_discrete_map={
            '人工智能词频数': '#10b981',
            '大数据词频数': '#f59e0b',
            '云计算词频数': '#8b5cf6',
            '区块链词频数': '#ec4899'
        },
        template='plotly_white'
    )
    fig.update_layout(
        title_font=dict(size=16, weight='bold'),
        plot_bgcolor='white',
        xaxis=dict(
            title='年份',
            tickvals=list(range(1999, 2024, 2)),  # 关键：range转列表
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title='平均词频数',
            gridcolor='#e5e7eb'
        ),
        legend_title='技术类型',
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig

# --------------------------
# 页面布局
# --------------------------
def main():
    st.markdown("<h1>📈 上市公司数字化转型全周期分析平台</h1>", unsafe_allow_html=True)
    st.divider()
    
    # 加载数据
    df = load_data()
    
    # 侧边栏（增强交互）
    with st.sidebar:
        st.markdown("<h2>🔍 企业精准查询</h2>", unsafe_allow_html=True)
        query_input = st.text_input(
            "输入股票代码/企业名称",
            placeholder="例如：600000 / 浦发银行",
            help="支持模糊查询，如输入“银行”匹配所有银行企业"
        )
        # 年份筛选器（可选）
        st.markdown("<h3 style='margin-top: 1.5rem;'>📅 年份范围</h3>", unsafe_allow_html=True)
        year_filter = st.slider(
            "选择查看年份",
            min_value=1999,
            max_value=2023,
            value=(1999, 2023),
            step=1
        )
        st.markdown("---")
        # 数据概览卡片（字体改为黑色）
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #000000; font-size: 1.2rem;'>数据概览</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #000000;'>📊 覆盖年份：1999-2023</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #000000;'>🏢 企业数量：{df['企业名称'].nunique()} 家</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #000000;'>📋 数据总量：{len(df):,} 条</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 主内容标签页
    tab1, tab2 = st.tabs(["🏢 企业全周期趋势", "📊 全市场整体分析"])
    
    # 标签1：企业全周期趋势（1999-2023完整数据）
    with tab1:
        st.markdown("<h2>企业1999-2023数字化转型全趋势</h2>", unsafe_allow_html=True)
        if query_input:
            company_data = get_company_full_data(df, query_input)
            if company_data is not None and not company_data['企业名称'].isna().all():
                # 企业信息卡片
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("股票代码", company_data['股票代码'].iloc[0])
                with col2:
                    st.metric("企业名称", company_data['企业名称'].iloc[0])
                with col3:
                    st.metric("所属行业", company_data['行业'].iloc[0])
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 全年份折线图（核心）
                st.markdown("<h3>1999-2023全指标趋势图</h3>", unsafe_allow_html=True)
                st.plotly_chart(plot_company_full_trend(company_data), use_container_width=True)
                
                # 详细数据表格（筛选年份）
                st.markdown("<h3>1999-2023详细数据</h3>", unsafe_allow_html=True)
                filtered_data = company_data[(company_data['年份'] >= year_filter[0]) & (company_data['年份'] <= year_filter[1])]
                st.dataframe(
                    filtered_data[['年份', '数字化转型指数', '人工智能词频数', '大数据词频数', '云计算词频数', '区块链词频数']].set_index('年份'),
                    use_container_width=True,
                    height=300
                )
            else:
                st.warning("⚠️ 未找到匹配的企业，请检查输入内容")
        else:
            st.info("💡 请在左侧输入股票代码或企业名称，查询其1999-2023年完整数据")
    
    # 标签2：全市场整体分析（1999-2023完整折线）
    with tab2:
        st.markdown("<h2>全市场1999-2023数字化转型趋势</h2>", unsafe_allow_html=True)
        
        # 全市场转型指数折线（带移动平均）
        st.markdown("<h3>全市场平均转型指数趋势</h3>", unsafe_allow_html=True)
        st.plotly_chart(plot_market_full_trend(df), use_container_width=True)
        
        # 全市场技术词频数对比折线
        st.markdown("<h3>全市场数字技术词频数趋势对比</h3>", unsafe_allow_html=True)
        st.plotly_chart(plot_tech_comparison(df), use_container_width=True)
        
        # 年度数据分布箱线图（增强分析）
        st.markdown("<h3>1999-2023年转型指数年度分布</h3>", unsafe_allow_html=True)
        box_fig = px.box(
            df,
            x='年份',
            y='数字化转型指数',
            title='各年度转型指数分布（箱线图）',
            width=900,
            height=400,
            template='plotly_white'
        )
        box_fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(
                tickvals=list(range(1999, 2024, 3)),  # 关键：range转列表
                tickangle=45, 
                gridcolor='#e5e7eb'
            ),
            yaxis=dict(gridcolor='#e5e7eb'),
            margin=dict(l=20, r=20, t=60, b=40)
        )
        st.plotly_chart(box_fig, use_container_width=True)

if __name__ == "__main__":
    main()