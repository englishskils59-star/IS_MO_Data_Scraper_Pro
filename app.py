import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="IS.MO Data Scraper Pro", layout="wide")

# -----------------------------
# Language toggle
# -----------------------------
lang = st.selectbox("Language / اللغة", ["English", "العربية"])

def t(en, ar):
    return en if lang == "English" else ar

# -----------------------------
# UI
# -----------------------------
st.title("🕷️ IS.MO Data Scraper Pro")

url = st.text_input(t("Website URL", "رابط الموقع"))
selector = st.text_input(
    t("CSS Selector (optional)", "CSS Selector (اختياري)"),
    placeholder="table, .class, #id"
)

data_type = st.selectbox(
    t("Data Type", "نوع البيانات"),
    ["Table", "Text", "Images"]
)

selected_date = st.date_input(
    t("Filter by date (optional)", "فلترة حسب التاريخ (اختياري)"),
    value=None
)

# -----------------------------
# Helper functions
# -----------------------------
def scrape_static(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def filter_by_date(data, selected_date):
    if not selected_date:
        return data

    date_str = selected_date.strftime("%Y-%m-%d")
    filtered = []

    for row in data:
        text = " ".join(row)
        if date_str in text:
            filtered.append(row)

    return filtered

# -----------------------------
# Scraping Logic
# -----------------------------
if st.button(t("Start Scraping", "ابدأ السحب")):
    if not url:
        st.error(t("Please enter a URL", "من فضلك أدخل رابط الموقع"))
    else:
        try:
            soup = scrape_static(url)

            # -------- TABLE --------
            if data_type == "Table":
                table = soup.select_one(selector) if selector else soup.find("table")

                if table is None:
                    st.warning(t("No table found on this page", "لا يوجد جدول في الصفحة"))
                else:
                    rows = []
                    for tr in table.find_all("tr"):
                        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                        if cells:
                            rows.append(cells)

                    rows = filter_by_date(rows, selected_date)

                    if not rows:
                        st.warning(t("No data matches the selected date", "لا توجد بيانات مطابقة للتاريخ"))
                    else:
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                        st.dataframe(df, use_container_width=True)

            # -------- TEXT --------
            elif data_type == "Text":
                elements = soup.select(selector) if selector else soup.find_all("p")

                texts = []
                for el in elements:
                    txt = el.get_text(strip=True)
                    if txt:
                        texts.append([txt])

                texts = filter_by_date(texts, selected_date)

                if not texts:
                    st.warning(t("No text found", "لم يتم العثور على نصوص"))
                else:
                    df = pd.DataFrame(texts, columns=[t("Text", "النص")])
                    st.dataframe(df, use_container_width=True)

            # -------- IMAGES --------
            elif data_type == "Images":
                images = soup.select(selector) if selector else soup.find_all("img")

                img_urls = []
                for img in images:
                    src = img.get("src")
                    if src and src.startswith("http"):
                        img_urls.append(src)

                if not img_urls:
                    st.warning(t("No images found", "لم يتم العثور على صور"))
                else:
                    st.image(img_urls, width=200)

        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("© IS.MO Data Scraper Pro | Personal Use")
