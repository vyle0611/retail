import os
import duckdb
import pandas as pd
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Retail Lakehouse Dashboard", layout="wide")

# Nếu Groq báo model bị gỡ, đổi tên model theo danh sách tại console.groq.com/docs/models
GROQ_MODEL = "llama-3.3-70b-versatile"

# ---------- Kết nối MotherDuck ----------
os.environ["MOTHERDUCK_TOKEN"] = st.secrets["MOTHERDUCK_TOKEN"]

@st.cache_resource
def get_conn():
    return duckdb.connect("md:retail_db")

@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    return get_conn().cursor().sql(sql).df()

# ---------- Dữ liệu ----------
daily = query("""
    SELECT CAST(event_date AS DATE) AS date,
           SUM(total_revenue) AS revenue,
           SUM(total_orders)  AS orders
    FROM retail_db.main.fct_daily_sales
    GROUP BY 1 ORDER BY 1
""")

top_cat = query("""
    SELECT category_code, SUM(total_revenue) AS revenue, SUM(total_orders) AS orders
    FROM retail_db.main.fct_daily_sales
    GROUP BY 1 ORDER BY 2 DESC LIMIT 10
""")

# ---------- Giao diện ----------
st.title(" Retail Lakehouse Dashboard")
st.caption("Dữ liệu: MotherDuck (tầng Gold) • Mô hình gợi ý: ALS + LightGBM • Phân tích: Llama 3 qua Groq")

c1, c2, c3 = st.columns(3)
c1.metric("Tổng doanh thu", f"${daily.revenue.sum():,.0f}")
c2.metric("Tổng đơn hàng", f"{int(daily.orders.sum()):,}")
c3.metric("Số ngày dữ liệu", f"{len(daily)}")

st.subheader("Doanh thu theo ngày")
st.line_chart(daily.set_index("date")["revenue"])

st.subheader("Top 10 danh mục theo doanh thu")
st.bar_chart(top_cat.set_index("category_code")["revenue"])

# ---------- Gợi ý sản phẩm ----------
st.divider()
st.subheader("Gợi ý sản phẩm cho khách hàng")
users = query("SELECT DISTINCT user_id FROM retail_db.main.gold_recommendations ORDER BY 1").user_id.tolist()
uid = st.selectbox("Chọn user_id", users)
recs = query(f"""
    SELECT rank, product_id, category_code, brand,
           ROUND(avg_price, 2) AS avg_price, ROUND(score, 4) AS score
    FROM retail_db.main.gold_recommendations
    WHERE user_id = {int(uid)}
    ORDER BY rank
""")
st.dataframe(recs, use_container_width=True, hide_index=True)

# ---------- GenAI: gợi ý nhập hàng ----------
st.divider()
st.subheader("Phân tích bằng AI: mặt hàng cần nhập thêm")

if st.button("Phân tích bằng AI"):
    with st.spinner("Đang phân tích..."):
        trend = query("""
            WITH mx AS (SELECT MAX(CAST(event_date AS DATE)) AS d FROM retail_db.main.fct_daily_sales)
            SELECT category_code,
                   ROUND(SUM(CASE WHEN CAST(event_date AS DATE) > d - 7 THEN total_revenue END), 0) AS revenue_last_7d,
                   ROUND(SUM(CASE WHEN CAST(event_date AS DATE) <= d - 7 THEN total_revenue END), 0) AS revenue_prev_7d,
                   SUM(CASE WHEN CAST(event_date AS DATE) > d - 7 THEN total_orders END) AS orders_last_7d
            FROM retail_db.main.fct_daily_sales, mx
            WHERE CAST(event_date AS DATE) > d - 14
            GROUP BY category_code
            ORDER BY revenue_last_7d DESC NULLS LAST
            LIMIT 10
        """)
        top_prod = query("""
            SELECT p.product_id, p.category_code, p.brand,
                   COUNT(*) AS units_sold, ROUND(SUM(f.revenue), 0) AS revenue
            FROM retail_db.main.fct_purchases f
            JOIN retail_db.main.dim_product p USING (product_id)
            GROUP BY 1, 2, 3
            ORDER BY revenue DESC
            LIMIT 10
        """)

        prompt = f"""Bạn là chuyên gia phân tích bán lẻ thương mại điện tử.
Dưới đây là dữ liệu doanh thu (đơn vị USD).

[Xu hướng 10 danh mục hàng đầu: 7 ngày gần nhất so với 7 ngày trước đó]
{trend.to_string(index=False)}

[Top 10 sản phẩm theo doanh thu]
{top_prod.to_string(index=False)}

Dựa trên dữ liệu trên, hãy cho biết 3 mặt hàng/danh mục cần nhập thêm và giải thích lý do
(dẫn số liệu cụ thể). Trả lời bằng tiếng Việt, ngắn gọn, đánh số 1-2-3."""

        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            st.markdown(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"Không gọi được Groq: {e}")

        with st.expander("Dữ liệu đã gửi cho AI"):
            st.dataframe(trend, hide_index=True)
            st.dataframe(top_prod, hide_index=True)
