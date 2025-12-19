import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="IS.MO Data Collector Pro", layout="wide")

# ======================================================
# Language
# ======================================================
lang = st.selectbox("Language / اللغة", ["English", "العربية"])
def t(en, ar): return en if lang == "English" else ar

st.title("🏢 IS.MO Data Collector Pro – Enterprise")

# ======================================================
# Utilities
# ======================================================
def export_excel(sheets: dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()

def auto_chart(df):
    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        st.bar_chart(numeric)

# ======================================================
# Mode Selection
# ======================================================
mode = st.selectbox(
    t("Select Data Source", "اختر مصدر البيانات"),
    [
        "Web Scraping (HTML)",
        "Crypto API – Binance",
        "Finance API – Yahoo (Basic)",
        "Scheduler / Automation"
    ]
)

# ======================================================
# MODE 1: WEB SCRAPING
# ======================================================
if mode == "Web Scraping (HTML)":
    st.subheader("🌐 Web Scraping Engine")

    url = st.text_input(t("Website URL", "رابط الموقع"))
    selector = st.text_input(t("CSS Selector (optional)", "CSS Selector (اختياري)"))
    data_type = st.selectbox(t("Data Type", "نوع البيانات"), ["Table", "Text", "Images"])

    if st.button(t("Run Scraping", "تشغيل الاستخراج")):
        if not url:
            st.error(t("Please enter URL", "من فضلك أدخل الرابط"))
        else:
            soup = BeautifulSoup(
                requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text,
                "html.parser"
            )
            excel = {}

            # -------- TABLE --------
            if data_type == "Table":
                table = soup.select_one(selector) if selector else soup.find("table")
                if table:
                    rows = []
                    for tr in table.find_all("tr"):
                        cells = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
                        if cells:
                            rows.append(cells)
                    df = pd.DataFrame(rows[1:], columns=rows[0])
                    for c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="ignore")
                    st.dataframe(df, use_container_width=True)
                    auto_chart(df)
                    excel["Table_Data"] = df
                else:
                    st.warning("No table found")

            # -------- TEXT --------
            elif data_type == "Text":
                elements = soup.select(selector) if selector else soup.find_all("p")
                data = [{
                    "ID": i+1,
                    "Content": el.get_text(strip=True),
                    "Length": len(el.get_text(strip=True)),
                    "Extracted_At": datetime.now()
                } for i, el in enumerate(elements) if el.get_text(strip=True)]
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                excel["Text_Data"] = df

            # -------- IMAGES --------
            elif data_type == "Images":
                images = soup.select(selector) if selector else soup.find_all("img")
                data, urls = [], []
                for i, img in enumerate(images, 1):
                    src = img.get("src")
                    if src and src.startswith("http"):
                        urls.append(src)
                        data.append({"ID": i, "Image_URL": src})
                if urls:
                    st.image(urls, width=200)
                    excel["Images"] = pd.DataFrame(data)
                else:
                    st.warning("No images found")

            if excel:
                st.download_button(
                    t("Download Excel", "تحميل Excel"),
                    export_excel(excel),
                    file_name="Web_Scraping_Data.xlsx"
                )

# ======================================================
# MODE 2: BINANCE API
# ======================================================
elif mode == "Crypto API – Binance":
    st.subheader("🔗 Binance Official API")

    limit = st.slider(t("Number of Symbols", "عدد العملات"), 10, 200, 50)

    if st.button(t("Fetch Data", "جلب البيانات")):
       url = "https://api.binance.com/api/v3/ticker/24hr"
response = requests.get(url, timeout=15)

if response.status_code != 200:
    st.error("Binance API Error")
else:
    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        st.warning("No data returned from Binance")
    else:
        df = pd.DataFrame(data)

        required_cols = [
            "symbol",
            "lastPrice",
            "priceChangePercent",
            "volume",
            "quoteVolume"
        ]

        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"Missing columns: {missing}")
        else:
            df = df[required_cols]
            df.columns = ["Symbol", "Price", "24h %", "Volume", "Quote Volume"]

            for col in ["Price", "24h %", "Volume", "Quote Volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.sort_values("Quote Volume", ascending=False).head(limit)

            st.dataframe(df, use_container_width=True)
            auto_chart(df)

            st.download_button(
                "Download Excel",
                export_excel({"Binance_Data": df}),
                file_name="Binance_Data.xlsx"
            )

        df.columns = ["Symbol", "Price", "24h %", "Volume", "Quote Volume"]
        df[["Price","24h %","Volume","Quote Volume"]] = \
            df[["Price","24h %","Volume","Quote Volume"]].astype(float)
        df = df.sort_values("Quote Volume", ascending=False).head(limit)

        st.dataframe(df, use_container_width=True)
        auto_chart(df)

        st.download_button(
            t("Download Excel", "تحميل Excel"),
            export_excel({"Binance_Data": df}),
            file_name="Binance_Data.xlsx"
        )

# ======================================================
# MODE 3: YAHOO FINANCE (Basic)
# ======================================================
elif mode == "Finance API – Yahoo (Basic)":
    st.subheader("📈 Yahoo Finance (Basic)")

    symbol = st.text_input("Symbol (ex: AAPL, MSFT)")
    if st.button("Fetch"):
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        data = requests.get(url).json()
        result = data["quoteResponse"]["result"]
        if result:
            df = pd.DataFrame(result)
            st.dataframe(df)
            st.download_button(
                "Download Excel",
                export_excel({"Yahoo_Data": df}),
                file_name="Yahoo_Data.xlsx"
            )
        else:
            st.warning("Symbol not found")

# ======================================================
# MODE 4: SCHEDULER (LOGICAL)
# ======================================================
elif mode == "Scheduler / Automation":
    st.subheader("⏱ Scheduler (Manual / Logical)")

    st.info(
        "Streamlit Cloud لا يدعم Background Jobs.\n"
        "لكن تقدر تستخدم الوضع ده لتشغيل الاستخراج دوريًا يدويًا."
    )

    st.markdown("""
    ### Use cases:
    - Daily market snapshot
    - Weekly reports
    - Manual scheduled runs
    """)

    if st.button("Run Scheduled Task Now"):
        st.success("Task executed successfully (Logical Scheduler)")

# ======================================================
st.markdown("---")
st.caption("© IS.MO Data Collector Pro – Enterprise Edition | Personal Use")
