import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="IS.MO Data Scraper Pro", layout="wide")

st.title("📊 IS.MO Data Scraper Pro")
st.write("Web Scraping + APIs → Excel + Charts (Auto)")

mode = st.selectbox(
    "اختر مصدر البيانات",
    [
        "Web Scraping (Static Sites)",
        "Finance API - Yahoo (Basic)"
    ]
)

# =========================
# Web Scraping
# =========================
if mode == "Web Scraping (Static Sites)":
    url = st.text_input("رابط الموقع")
    tag = st.text_input("HTML Tag (مثال: div, span, img)")
    class_name = st.text_input("Class (اختياري)")

    if st.button("جلب البيانات"):
        if url and tag:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")

            elements = soup.find_all(tag, class_=class_name if class_name else None)

            data = []
            images = []

            for el in elements:
                text = el.get_text(strip=True)
                if text:
                    data.append(text)

                if el.name == "img" and el.get("src"):
                    images.append(el.get("src"))

            df = pd.DataFrame({"Text Data": data})

            st.success("تم الاستخراج بنجاح ✅")

            st.subheader("📄 البيانات")
            st.dataframe(df)

            # Chart تلقائي
            if len(df) > 0:
                st.subheader("📈 Chart تلقائي")
                fig, ax = plt.subplots()
                df["Text Data"].value_counts().head(10).plot(kind="bar", ax=ax)
                st.pyplot(fig)

            # Images
            if images:
                st.subheader("🖼️ الصور")
                for img in images[:10]:
                    st.image(img)

            # Export Excel
            st.download_button(
                "⬇️ تحميل Excel",
                df.to_excel(index=False),
                file_name="scraped_data.xlsx"
            )

# =========================
# Yahoo Finance API
# =========================
elif mode == "Finance API - Yahoo (Basic)":
    ticker = st.text_input("Ticker (مثال: BTC-USD , AAPL)")

    if st.button("جلب البيانات"):
        if ticker:
            data = yf.Ticker(ticker).history(period="1mo")
            data.reset_index(inplace=True)

            st.success("تم جلب البيانات بنجاح ✅")
            st.dataframe(data)

            # Chart تلقائي
            st.subheader("📈 سعر الإغلاق")
            fig, ax = plt.subplots()
            ax.plot(data["Date"], data["Close"])
            ax.set_xlabel("Date")
            ax.set_ylabel("Close Price")
            st.pyplot(fig)

            # Export Excel
            st.download_button(
                "⬇️ تحميل Excel",
                data.to_excel(index=False),
                file_name=f"{ticker}_data.xlsx"
            )
