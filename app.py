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
data_type = st.selectbox(t("Data Type", "نوع البيانات"), ["Table", "Text"])
chart_type = st.selectbox(t("Chart Type", "نوع الشارت"), ["Bar", "Line"])
selected_date = st.date_input(t("Filter by date (optional)", "فلترة حسب التاريخ"), value=None)

# =====================
# Helpers
# =====================
def scrape_static(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def filter_by_date(df, selected_date):
    if selected_date is None:
        return df
    date_str = selected_date.strftime("%Y-%m-%d")
    return df[df.apply(lambda r: r.astype(str).str.contains(date_str).any(), axis=1)]

def export_excel(dfs):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in dfs.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return output.getvalue()

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
                    df = filter_by_date(df, selected_date)

                    st.subheader(t("Data Preview", "معاينة البيانات"))
                    st.dataframe(df, use_container_width=True)

                    excel_sheets["Table_Data"] = df

                    if df.shape[1] >= 2:
                        x_col = st.selectbox(t("X Axis", "محور X"), df.columns)
                        y_col = st.selectbox(t("Y Axis", "محور Y"), df.columns)

                        st.subheader(t("Chart", "الشارت"))
                        chart_df = df[[x_col, y_col]].set_index(x_col)

                        if chart_type == "Bar":
                            st.bar_chart(chart_df)
                        else:
                            st.line_chart(chart_df)

            # ========== TEXT ==========
            elif data_type == "Text":
                elements = soup.select(selector) if selector else soup.find_all("p")
                texts = []
                for i, el in enumerate(elements, start=1):
                    txt = el.get_text(strip=True)
                    if txt:
                        texts.append({
                            "ID": i,
                            "Content": txt,
                            "Length": len(txt),
                            "Extracted_Date": datetime.now().strftime("%Y-%m-%d")
                        })

                df = pd.DataFrame(texts)
                df = filter_by_date(df, selected_date)

                st.subheader(t("Text Data Preview", "معاينة النصوص"))
                st.dataframe(df, use_container_width=True)

                excel_sheets["Text_Data"] = df

            # ========== EXPORT ==========
            if excel_sheets:
                st.subheader(t("Export", "تصدير"))
                st.download_button(
                    t("Download Excel (Professional)", "تحميل Excel احترافي"),
                    export_excel(excel_sheets),
                    file_name="ISMO_Data.xlsx"
                )

                for name, df in excel_sheets.items():
                    st.download_button(
                        f"Download {name} CSV",
                        df.to_csv(index=False),
                        file_name=f"{name}.csv"
                    )

        except Exception as e:
            st.error(str(e))

st.markdown("---")
st.caption("© IS.MO Data Scraper Pro | Personal Use")
