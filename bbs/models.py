from sqlalchemy import Column, Index, Integer, String, DateTime, Text
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    thread_id = Column(BIGINT(unsigned=True), nullable=True)
    name = Column(String(32), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime)
    file_hashs = Column(LONGTEXT, nullable=True)
    file_names = Column(LONGTEXT, nullable=True)
    file_name_originals = Column(LONGTEXT, nullable=True)
    ipaddress = Column(Text, nullable=False)

    # インデックス
    __table_args__ = (
        Index("idx_thread_id", "thread_id"),
    )
