import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px

st.set_page_config(
    page_title="IS.MO Data Scraper Pro",
    layout="wide"
)

# =====================
# Language
# =====================
lang = st.sidebar.selectbox("Language / اللغة", ["English", "العربية"])

def t(en, ar):
    return en if lang == "English" else ar

# =====================
# UI
# =====================
st.title("IS.MO Data Scraper Pro")

url = st.text_input(t("Website URL", "رابط الموقع"))
data_type = st.selectbox(
    t("Data Type", "نوع البيانات"),
    ["Table", "Text", "Images"]
)

selector = st.text_input(
    t("CSS Selector (optional)", "CSS Selector (اختياري)")
)

# =====================
# Scraper
# =====================
def scrape_static(url, selector, data_type):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    html = requests.get(url, headers=headers, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    if data_type == "Text":
        elements = soup.select(selector) if selector else soup.find_all(text=True)
        return [el.strip() for el in elements if el.strip()]

    if data_type == "Images":
        images = soup.select(selector) if selector else soup.find_all("img")
        return [img.get("src") for img in images if img.get("src")]

    if data_type == "Table":
        table = soup.select_one(selector) if selector else soup.find("table")
        rows = []
        for tr in table.find_all("tr"):
            rows.append([td.get_text(strip=True) for td in tr.find_all(["td", "th"])])
        return rows

# =====================
# Run Button
# =====================
if st.button(t("Run Scraping", "تشغيل الاستخراج")):

    if not url:
        st.warning(t("Please enter a URL", "من فضلك أدخل رابط الموقع"))
    else:
        try:
            with st.spinner(t("Scraping in progress...", "جاري الاستخراج...")):
                data = scrape_static(url, selector, data_type)

            if not data:
                st.warning(t("No data found", "لم يتم العثور على بيانات"))
            
            # ===== TABLE =====
            elif data_type == "Table":
                df = pd.DataFrame(data[1:], columns=data[0])
                st.subheader(t("Preview", "معاينة"))
                st.dataframe(df.head(50), use_container_width=True)

                if df.shape[1] >= 2:
                    fig = px.bar(
                        df,
                        x=df.columns[0],
                        y=df.columns[1],
                        title=t("Chart", "رسم بياني")
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.download_button(
                    t("Download CSV", "تحميل CSV"),
                    df.to_csv(index=False),
                    "data.csv"
                )

            # ===== TEXT =====
            elif data_type == "Text":
                df = pd.DataFrame(data, columns=["Text"])
                st.subheader(t("Preview", "معاينة"))
                st.dataframe(df.head(50), use_container_width=True)

                st.download_button(
                    t("Download CSV", "تحميل CSV"),
                    df.to_csv(index=False),
                    "text.csv"
                )

            # ===== IMAGES =====
            elif data_type == "Images":
                st.subheader(t("Preview", "معاينة"))
                for img in data[:20]:
                    st.image(img)

                df = pd.DataFrame(data, columns=["Image URL"])
                st.download_button(
                    t("Download CSV", "تحميل CSV"),
                    df.to_csv(index=False),
                    "images.csv"
                )

        except Exception as e:
            st.error(str(e))
