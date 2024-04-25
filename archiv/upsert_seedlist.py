from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, Boolean, BigInteger
from sqlalchemy.dialects.mysql import LONGTEXT, insert
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from time import gmtime, strftime
import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from src.database.database_connection import database_connection
from src.database.database_structure import SeedList


# Define the database structure
current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

def split_url(url):
    whole_name = url.split("/")[-1]
    xi = whole_name.split("-")
    if "_" in xi[-1]:
        xi[-1] = xi[-1].split("_")[0]
    id = xi[0]
    name = "_".join(xi[1:])
        
    return id, name

# Create tables according to class
engine = create_engine(database_connection(), echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Create a session instance
session = Session()

with open("data/seedlist_manual_all_140424.txt") as f:
    
    for line in f:
        url = f.readline()
        id, name = split_url(url)
        insert_stmt = insert(SeedList).values(ini_id = id, ini_name = name, seed_list_update = current_time)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(ini_name=insert_stmt.inserted.ini_name,
                                                                    seed_list_update = insert_stmt.inserted.seed_list_update)

        session.execute(on_duplicate_key_stmt)

# Commit the session to save records to database
session.commit()
session.close()
