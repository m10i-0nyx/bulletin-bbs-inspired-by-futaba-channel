import io
import streamlit as st
import hashlib
import os
import json
from datetime import datetime

from streamlit_paste_button import paste_image_button as pbutton
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

st.set_page_config(page_title="掲示板 : スレッド", page_icon="📝", layout="wide")

thread_id = st.query_params.get("tid")
if not thread_id:
    st.error("スレッドIDが指定されていません")
    st.write('<a href="/catalog" target="_self">カタログ</a>からスレッドを指定してください', unsafe_allow_html=True)
else:
    # 投稿一覧表示
    db = SessionLocal()
    posts = db.query(Post).filter(Post.thread_id == thread_id).order_by(Post.id.asc()).all()
    db.close()
    for idx, post in enumerate(posts):
        if idx == 0:
            st.set_page_config(page_title=str(post.message)[:32], page_icon="📝")
            st.header(post.message[:32])

        st.markdown(f"Name: **{post.name}** ({post.created_at.strftime('%Y-%m-%d %H:%M:%S')}) ID: *{post.id}*")
        # 横並びレイアウト

        with st.container():
            if post.file_names is not None:
                file_names = json.loads(post.file_names) # type: ignore
                file_name_originals = json.loads(post.file_name_originals) # type: ignore
                for idx, file_name in enumerate(file_names):
                    cols = st.columns([1, 3])  # [画像/動画, テキスト]
                    with cols[0]:
                        file_path = os.path.join(save_dir, str(file_name))
                        if file_name.lower().endswith((".png", ".jpeg", ".gif", ".webp")):
                            st.markdown(
                                f'''
                                <img src="/uploaded/{file_name}" alt="{file_name_originals[idx]}" width="200" /><br>
                                <a href="/uploaded/{file_name}">{file_name}</a>
                                ''',
                                unsafe_allow_html=True
                            )
                        elif file_name.lower().endswith((".mp4", ".avi")):
                            st.markdown(
                                f'''
                                <video src="/uploaded/{file_name}" width="200" controls>
                                お使いのブラウザは video タグをサポートしていません。
                                </video><br>
                                <a href="/uploaded/{file_name}">{file_name}</a>
                                ''',
                                unsafe_allow_html=True
                            )
                    if idx == 0:
                        with cols[1]:
                            st.markdown(post.message)
            else:
                st.markdown(post.message)
        st.markdown("---")

    if posts:
        with st.form("post_form", clear_on_submit=True):
            name = st.text_input("名前", max_chars=32, value=preset_post_name)
            message = st.text_area("メッセージ", max_chars=2048)
            uploaded_files = st.file_uploader("ファイルをアップロード（任意）", accept_multiple_files=True, type=["gif", "jpg", "png", "mp4", "avi", "webp"])
            submitted = st.form_submit_button("投稿")

            if submitted and (message != "" or uploaded_files):
                if name is None or name == "":
                    name = preset_post_name
                if message is None or message == "":
                    message = "ｷﾀ━━━(ﾟ∀ﾟ)━━━!!"

                post_id = None
                db = SessionLocal()
                try:
                    post = Post(
                        thread_id=thread_id,
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
                    st.rerun()
                finally:
                    db.close()

            elif submitted:
                st.warning("メッセージまたはファイルをアップロードしてください。")

        with st.container():
            paste_result = pbutton("📋 クリップボードから画像即うｐ", errors="raise")
            if paste_result.image_data is not None:
                st.info('クリップボードの画像プレビュー:')
                st.image(paste_result.image_data, width=300) # type: ignore

                if st.button(f"名前:{preset_post_name} で投稿してもよい？", icon=":material/warning:"):
                    name = None
                    message = None
                    if name is None or name == "":
                        name = preset_post_name
                    if message is None or message == "":
                        message = "ｷﾀ━━━(ﾟ∀ﾟ)━━━!!"

                    img_bytes = io.BytesIO()
                    paste_result.image_data.save(img_bytes, format='PNG') # type: ignore
                    file_bytes = img_bytes.getvalue() # Image as bytes
                    file_hash = hashlib.sha256(file_bytes).hexdigest()

                    db = SessionLocal()
                    try:
                        post = Post(
                            thread_id=thread_id,
                            name=name,
                            message=message,
                            created_at=datetime.now(),
                            file_hashs=json.dumps([file_hash]),
                            file_name_originals=json.dumps(["Clipboard"]),
                            ipaddress=st.context.headers.get("X-Forwarded-For", "unknown")
                        )
                        db.add(post)
                        db.commit()
                        db.refresh(post)
                        post_id = post.id

                        file_name = f"{post_id}.png"
                        save_path = os.path.join(save_dir, file_name)
                        with open(save_path, "wb") as fp:
                            fp.write(file_bytes)

                        post.file_names = json.dumps([file_name]) # type: ignore
                        db.commit()

                        st.success("投稿が完了しました！")
                        st.rerun()

                    finally:
                        db.close()
