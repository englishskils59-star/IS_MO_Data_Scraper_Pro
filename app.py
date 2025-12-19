import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="IS.MO Data Scraper Pro", layout="wide")

# =====================
# Language
# =====================
lang = st.selectbox("Language / اللغة", ["English", "العربية"])
def t(en, ar): return en if lang == "English" else ar

st.title("🚀 IS.MO Data Scraper Pro")

# =====================
# Inputs
# =====================
url = st.text_input(t("Website URL", "رابط الموقع"))
selector = st.text_input(t("CSS Selector (optional)", "CSS Selector (اختياري)"))
data_type = st.selectbox(
    t("Data Type", "نوع البيانات"),
    ["Table", "Text", "Images"]
)
chart_type = st.selectbox(t("Chart Type", "نوع الشارت"), ["Bar", "Line"])

# =====================
# Helpers
# =====================
def scrape_static(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def export_excel(sheets):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return output.getvalue()

def auto_chart(df, chart_type):
    numeric_cols = df.select_dtypes(include="number").columns
    if len(df.columns) >= 2 and len(numeric_cols) >= 1:
        x = df.columns[0]
        y = numeric_cols[0]
        chart_df = df[[x, y]].set_index(x)
        if chart_type == "Bar":
            st.bar_chart(chart_df)
        else:
            st.line_chart(chart_df)

# =====================
# Run
# =====================
if st.button(t("Run Scraping", "تشغيل الاستخراج")):
    if not url:
        st.error(t("Please enter URL", "من فضلك أدخل الرابط"))
    else:
        try:
            soup = scrape_static(url)
            excel_sheets = {}

            # ========== TABLE ==========
            if data_type == "Table":
                table = soup.select_one(selector) if selector else soup.find("table")
                if table is None:
                    st.warning(t("No table found", "لا يوجد جدول"))
                else:
                    rows = []
                    for tr in table.find_all("tr"):
                        cells = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
                        if cells:
                            rows.append(cells)

                    df = pd.DataFrame(rows[1:], columns=rows[0])
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="ignore")

                    st.subheader(t("Data Preview", "معاينة البيانات"))
                    st.dataframe(df, use_container_width=True)

                    st.subheader(t("Auto Chart", "الشارت التلقائي"))
                    auto_chart(df, chart_type)

                    excel_sheets["Table_Data"] = df

            # ========== TEXT ==========
            elif data_type == "Text":
                elements = soup.select(selector) if selector else soup.find_all("p")
                data = []
                for i, el in enumerate(elements, start=1):
                    txt = el.get_text(strip=True)
                    if txt:
                        data.append({
                            "ID": i,
                            "Content": txt,
                            "Length": len(txt),
                            "Extracted_At": datetime.now().strftime("%Y-%m-%d")
                        })

                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                excel_sheets["Text_Data"] = df

            # ========== IMAGES ==========
            elif data_type == "Images":
                images = soup.select(selector) if selector else soup.find_all("img")
                img_data = []
                img_urls = []

                for i, img in enumerate(images, start=1):
                    src = img.get("src")
                    if src and src.startswith("http"):
                        img_urls.append(src)
                        img_data.append({
                            "ID": i,
                            "Image_URL": src
                        })

                if img_urls:
                    st.subheader(t("Images Preview", "معاينة الصور"))
                    st.image(img_urls, width=200)

                    df = pd.DataFrame(img_data)
                    excel_sheets["Images"] = df
                else:
                    st.warning(t("No images found", "لا توجد صور"))

            # ========== EXPORT ==========
            if excel_sheets:
                st.subheader(t("Export", "تصدير"))
                st.download_button(
                    t("Download Excel (All Data)", "تحميل Excel كامل"),
                    export_excel(excel_sheets),
                    file_name="ISMO_Data_Scraper.xlsx"
                )

        except Exception as e:
            st.error(str(e))

st.markdown("---")
st.caption("© IS.MO Data Scraper Pro | Personal Use")
