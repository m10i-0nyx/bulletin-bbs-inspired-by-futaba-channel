import streamlit as st
from dotenv import load_dotenv

load_dotenv()

readme = st.Page(page="contents/readme.py", title="はじめに", icon=":material/article:", default=True)
catalog = st.Page(page="contents/catalog.py", title="カタログ", icon=":material/article:")
thread = st.Page(page=f"contents/thread.py", title="スレッド", icon=":material/article:")
thread_new = st.Page(page=f"contents/thread_new.py", title="スレッド新規作成", icon=":material/article:")
#develop = st.Page(page=f"contents/develop.py", title="実験場", icon=":material/warning:")
navigation_pages = [readme, catalog, thread, thread_new]

pg = st.navigation(navigation_pages) # type: ignore
pg.run()
