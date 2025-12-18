from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

URL_DATABASE='mysql+pymysql://root:mohan%4028169@localhost:3306/blogapplications'

engine=create_engine(URL_DATABASE)

SessionaLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()