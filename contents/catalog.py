import streamlit as st
import os
import math
import re
import json

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from bbs.models import Post


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
Post.metadata.create_all(bind=engine)

# 保存ディレクトリとデータファイル
save_dir = os.getenv("FILE_SAVE_DIR","uploaded")
os.makedirs(save_dir, exist_ok=True)

st.title("カタログ")
st.set_page_config(page_title="掲示板 : カタログ", page_icon="📝", layout="wide")

# 投稿一覧表示
db = SessionLocal()
posts = (
    db.query(
        Post.thread_id,
        func.count(Post.id).label("count")
    )
    .group_by(Post.thread_id)
    #.order_by(Post.thread_id.desc())
    .order_by(func.max(Post.id).desc())
    .all()
)

# テーブルで表示
cols_per_row = 4
rows = math.ceil(len(posts) / cols_per_row)
cell_pixel = 128

def strip_html_tags(text: str) -> str:
    """HTMLタグを除去する"""
    clean = re.sub(r'<.*?>', '', text)
    return clean

if posts:
    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            post_idx = row * cols_per_row + col_idx
            if post_idx >= len(posts):
                break

            post = db.query(Post).filter(Post.id == posts[post_idx].thread_id).one()
            res_count = posts[post_idx].count

            with cols[col_idx]:
                # HTMLタグ除去
                safe_message = strip_html_tags(str(post.message) or "")[:32]
                if post.file_names is not None:
                    file_names = json.loads(post.file_names) # type: ignore
                    file_name_originals = json.loads(post.file_name_originals) # type: ignore

                    # 最初1個目の画像をカタログに乗せる
                    file_name = file_names[0]
                    file_name_original = file_name_originals[0]

                    file_path = os.path.join(save_dir, str(file_name))
                    if file_name.lower().endswith((".png", ".jpeg", ".gif", ".webp")):
                        st.markdown(
                            f'''
                            <div style="width:{cell_pixel}px;height:{cell_pixel+16}px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                            <span style="position:absolute;top:2px;left:4px;font-size:1em;background:rgba(255,255,255,0.8);padding:1px 4px;border-radius:3px;">{res_count}</span>
                            <a href="/thread?tid={post.thread_id}" target="_self">
                                <img src="/uploaded/{file_name}" alt="{file_name_original}" width="{cell_pixel}" height="{cell_pixel}" style="object-fit:cover;" />
                                <span>{safe_message}</span>
                            </a>
                            </div>
                            ''',
                            unsafe_allow_html=True
                        )
                    elif file_name.lower().endswith((".mp4", ".avi")):
                        st.markdown(
                            f'''
                            <div style="width:{cell_pixel}px;height:{cell_pixel+16}px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                            <span style="position:absolute;top:2px;left:4px;font-size:1em;background:rgba(255,255,255,0.8);padding:1px 4px;border-radius:3px;">{res_count}</span>
                            <a href="/thread?tid={post.thread_id}" target="_self">
                            <video src="/uploaded/{file_name}" width="{cell_pixel}" height="{cell_pixel}" style="object-fit:cover;" controls>
                                お使いのブラウザは video タグをサポートしていません。
                            </video>
                            <span>{safe_message}</span>
                            </a>
                            </div>
                            ''',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        f'''
                        <div style="width:{cell_pixel}px;height:{cell_pixel+16}px;display:flex;align-items:center;justify-content:center;border:1px solid #eee;overflow:hidden;">
                        <span style="position:absolute;top:2px;left:4px;font-size:1em;background:rgba(255,255,255,0.8);padding:1px 4px;border-radius:3px;">{res_count}</span>
                        <a href="/thread?tid={post.thread_id}" target="_self">
                        <span>{safe_message}</span>
                        </a>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
else:
    st.info("まだスレッドがありません")

db.close()
