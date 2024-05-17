import pandas as pd
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects import mysql

from src.database.database_structure import Base


class Portal_Scraper():
    def __init__(self, connection : str, wait_time : int = 30) -> None:
        
        # Initalize Database and create tables according to classes in src.database.database_structure
        self.DATABASE_CONNECTION = connection
        
        # API Endpoints
        self.API_INI = "https://ec.europa.eu/info/law/better-regulation/brpapi/groupInitiatives/"
        self.API_FB = "https://ec.europa.eu/info/law/better-regulation/api/allFeedback?publicationId="
        self.API_ATTACHMENTS = "https://ec.europa.eu/info/law/better-regulation/api/download/"
        
        # website request wait time
        self.WAIT_TIME = wait_time
        
        # headers for website request
        headers = requests.utils.default_headers()
        headers['From'] = 'University of Hildesheim (bukold@uni-hildesheim.de)'
        self.HEADER = headers
                
    def init_database_session(self, create_db : bool = False):
        self.engine = create_engine(self.DATABASE_CONNECTION, echo=False, pool_pre_ping=True, pool_recycle=1600, connect_args={
                                                                                        'connect_timeout': 1600
                                                                                        #'max_execution_time' : 1600,
                                                                                        #'interactive_timeout' : 1600
                                                                                        }) #connection timeout in seconds
        
        Session = sessionmaker(bind=self.engine)
        # Create tables according to classes in src.database.database_structure
        if create_db is True:
            Base.metadata.create_all(self.engine)
            return Session, self.engine
        else:
            return Session, self.engine
            
            
    def sql_to_df(self, sql : str) -> pd.DataFrame:
        engine = create_engine(self.DATABASE_CONNECTION)
        df = pd.read_sql(sql, engine)
        return df
    
    def seedlist_get_ids(self, where : str) -> pd.Series:
        sql = "SELECT initiative_id FROM `seed_list` WHERE {}".format(where)
        seedlist = self.sql_to_df(sql)
        return seedlist["initiative_id"]
    
    def stages_get_ids(self) -> pd.Series:
        sql = "SELECT stage_id FROM `stages` WHERE stages.feedback_updated is Null AND stages.type != 'OPC_LAUNCHED' AND stages.total_feedback != 0"
        seedlist = self.sql_to_df(sql)
        return seedlist["stage_id"]
    
    def attachments_get_ids(self, where : str) -> pd.Series:
        sql = "SELECT document_id FROM `attachments` WHERE {}".format(where)
        seedlist = self.sql_to_df(sql)
        return seedlist["document_id"]

        
