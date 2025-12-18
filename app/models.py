from sqlalchemy import Column,Integer,String
from app.database import Base

class Posts(Base):
    __tablename__='Post'
    id=Column(Integer,primary_key=True, index=True)
    content=Column(String(100))
    user_id=Column(Integer)
