
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="IS.MO Data Scraper Pro", layout="wide")

# Language
lang = st.sidebar.selectbox("Language / اللغة", ["English", "العربية"])

def t(en, ar):
    return en if lang == "English" else ar

st.title(t("IS.MO Data Scraper Pro", "IS.MO Data Scraper Pro"))

url = st.text_input(t("Website URL", "رابط الموقع"))
data_type = st.selectbox(t("Data Type", "نوع البيانات"), ["Table", "Text", "Images"])
selector = st.text_input(t("CSS Selector (optional)", "CSS Selector (اختياري)"))

def static_scrape(url, selector, data_type):
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")
    els = soup.select(selector) if selector else soup.find_all()

    if data_type == "Text":
        return [el.get_text(strip=True) for el in els if el.get_text(strip=True)]

    if data_type == "Images":
        return [el.get("src") for el in els if el.name == "img" and el.get("src")]

    if data_type == "Table":
        table = soup.select_one(selector) if selector else soup.find("table")
        rows = []
        for tr in table.find_all("tr"):
            rows.append([td.get_text(strip=True) for td in tr.find_all(["td","th"])])
        return rows

def dynamic_scrape(url, selector, data_type):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_selector(selector)
        els = page.query_selector_all(selector)

        if data_type == "Text":
            data = [el.inner_text() for el in els]
        elif data_type == "Images":
            data = [el.get_attribute("src") for el in els]
        else:
            data = []
        browser.close()
        return data

if st.button(t("Run Scraping", "تشغيل الاستخراج")):
    if not url:
        st.warning(t("Please enter a URL", "من فضلك أدخل رابط الموقع"))
    else:
        try:
            with st.spinner(t("Scraping in progress...", "جاري الاستخراج...")):
                try:
                    data = static_scrape(url, selector, data_type)
                except Exception:
                    data = dynamic_scrape(url, selector, data_type)

            if data_type == "Table":
                df = pd.DataFrame(data[1:], columns=data[0] if data else None)
                st.dataframe(df.head(50), use_container_width=True)

                if df.shape[1] >= 2:
                    fig = px.bar(df, x=df.columns[0], y=df.columns[1])
                    st.plotly_chart(fig, use_container_width=True)

                st.download_button("Download CSV", df.to_csv(index=False), "data.csv")

            elif data_type == "Text":
                st.write(data[:50])
                df = pd.DataFrame(data, columns=["Text"])
                st.download_button("Download CSV", df.to_csv(index=False), "text.csv")

            elif data_type == "Images":
                for img in data[:20]:
                    st.image(img)
                df = pd.DataFrame(data, columns=["Image URL"])
                st.download_button("Download CSV", df.to_csv(index=False), "images.csv")

        except Exception as e:
            st.error(str(e))
