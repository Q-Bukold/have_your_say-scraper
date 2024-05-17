from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime
import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from ..hys_portal_scraper import Portal_Scraper
from src.database.database_structure import SeedList

class SeedList_Handler(Portal_Scraper):
    def __init__(self, connection: str) -> None:
        super().__init__(connection)
        
        self.Session, engine = super().init_database_session()
    
    def insert_seedlist(self, filename:str):
        '''
        Upserts a seedlist to MySQL Database configured in database_connection.py.
        This step is required before using the other scrapers.
        
        filename : Path to a .txt-file where each line contains one URL to an Initative Homepage.
        like: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14215-Traineeships-proposed-Directive_en
        '''
        
        with self.Session() as sess:
            current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            
            with open(filename) as f:
                for line in f:
                    url = f.readline()
                    id, name = self._split_url(url)
                    insert_stmt = insert(SeedList).values(initiative_id = id, initiative_name = name, seed_list_updated = current_time)
                    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(initiative_name=insert_stmt.inserted.initiative_name,
                                                                                seed_list_updated = insert_stmt.inserted.seed_list_updated)

                    sess.execute(on_duplicate_key_stmt)
            # Commit the session to save records to database
            sess.commit()

    
    def _split_url(self, url):
        whole_name = url.split("/")[-1]
        xi = whole_name.split("-")
        if "_" in xi[-1]:
            xi[-1] = xi[-1].split("_")[0]
        id = xi[0]
        name = "_".join(xi[1:])
            
        return id, name
    
    
    