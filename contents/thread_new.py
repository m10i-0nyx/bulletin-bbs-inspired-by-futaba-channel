import random
import string
import streamlit as st
import hashlib
import os
import json
from datetime import datetime

from captcha.image import ImageCaptcha
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bbs.models import Post

preset_post_name = os.getenv("PRESET_POST_NAME","としあき")

db_config: dict = {
    "protocol": "mysql+pymysql",
    "username": os.getenv("MYSQL_USERNAME","bbs"),
    "password": os.getenv("MYSQL_PASSWORD","bbspw!"),
    "hostname": os.getenv("MYSQL_HOSTNAME","localhost"),
    "port"    : int(os.getenv("MYSQL_PORT", 3306)),
    "dbname"  : os.getenv("MYSQL_DATABASE","bbs"),
    "charset" : "utf8mb4"
}
sqlalchemy_db_url: str = "{protocol:s}://{username:s}:{password:s}@{hostname:s}:{port:d}/{dbname:s}?charset={charset:s}".\
    format(**db_config)

# 追加: DBセッション作成
engine = create_engine(sqlalchemy_db_url, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 保存ディレクトリとデータファイル
save_dir = os.getenv("FILE_SAVE_DIR","uploaded")
os.makedirs(save_dir, exist_ok=True)

st.title("スレッド新規作成")
st.set_page_config(page_title="掲示板 : スレッド新規作成", page_icon="📝", layout="wide")

@st.dialog("スレッドが作成されました")
def view_dialog(id):
    st.markdown(f"""
    スレッドが作成されました。<br>
    <a href="/thread?tid={id}" target="_self">スレッドを表示</a>
    """,
    unsafe_allow_html=True)

# 投稿フォーム
def main():
    with st.form("post_form", clear_on_submit=True):
        name = st.text_input("名前", max_chars=32, value=preset_post_name)
        message = st.text_area("メッセージ", max_chars=2048)
        uploaded_files = st.file_uploader("ファイルをアップロード（任意）", accept_multiple_files=True, type=["gif", "jpg", "png", "mp4", "avi", "webp"])
        submitted = st.form_submit_button(label="スレッド投稿", type="primary")

        if submitted and (message != "" or uploaded_files):
            if name is None or name == "":
                name = preset_post_name
            if message is None or message == "":
                message = "ｷﾀ━━━(ﾟ∀ﾟ)━━━!!"

            post_id = None
            db = SessionLocal()
            try:
                post = Post(
                    thread_id=None,
                    name=name,
                    message=message,
                    created_at=datetime.now(),
                    file_hashs=None,
                    file_name_originals=None,
                    ipaddress=st.context.headers.get("X-Forwarded-For", "unknown")
                )
                db.add(post)
                db.commit()
                db.refresh(post)
                post_id = post.id # save id
                if post.thread_id is None:
                    post.thread_id = post_id # parent post

                if uploaded_files:
                    file_hashs = []
                    file_names = []
                    file_name_originals = []

                    for idx, uploaded_file in enumerate(uploaded_files):
                        file_bytes = uploaded_file.read()
                        file_hash = hashlib.sha256(file_bytes).hexdigest()
                        file_ext = uploaded_file.type.split("/")[1]
                        file_name = f"{post_id}_{(idx+1):03d}.{file_ext}"
                        save_path = os.path.join(save_dir, file_name)
                        with open(save_path, "wb") as fp:
                            fp.write(file_bytes)

                        file_hashs.append(file_hash)
                        file_names.append(file_name)
                        file_name_originals.append(uploaded_file.name)

                    post.file_hashs = json.dumps(file_hashs) # type: ignore
                    post.file_names = json.dumps(file_names) # type: ignore
                    post.file_name_originals = json.dumps(file_name_originals) # type: ignore
                db.commit()

                st.success("投稿が完了しました！")

                # 再度 Captcha要求
                if 'controllo' in st.session_state:
                    del st.session_state['controllo']
            finally:
                db.close()

            if post_id is not None:
                view_dialog(post_id)

        elif submitted:
            st.warning("メッセージまたはファイルをアップロードしてください。")

def captcha_control():
    #control if the captcha is correct
    if 'controllo' not in st.session_state or st.session_state['controllo'] == False:
        with st.form("captcha_form", clear_on_submit=True):
            # define the session state for control if the captcha is correct
            st.session_state['controllo'] = False
            col1, col2 = st.columns(2)

            # define the session state for the captcha text because it doesn't change during refreshes
            if 'Captcha' not in st.session_state:
                    st.session_state['Captcha'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            captcha_text = str(st.session_state['Captcha'])

            #setup the captcha widget
            image = ImageCaptcha(width=300, height=150)
            data = image.generate(captcha_text)
            col1.image(data)
            input_captcha = col2.text_input(label="左の文字を入力してください(小文字でもOK)")
            submitted = col2.form_submit_button(label="コード確認", type="primary")

            if submitted:
                input_captcha = input_captcha.replace(" ", "").strip()
                # if the captcha is correct, the controllo session state is set to True
                if captcha_text.lower() == input_captcha.lower():
                    del st.session_state['Captcha']
                    col1.empty()
                    col2.empty()
                    st.session_state['controllo'] = True
                    st.rerun()
                else:
                    # if the captcha is wrong, the controllo session state is set to False and the captcha is regenerated
                    del st.session_state['Captcha']
                    del st.session_state['controllo']
                    st.rerun()
            else:
                #wait for the button click
                st.stop()

if 'controllo' not in st.session_state or st.session_state['controllo'] == False:
    captcha_control()
else:
    main()
