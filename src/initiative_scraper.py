import pandas as pd
import requests
import json
from json import JSONDecodeError
import time

from sqlalchemy import update
from time import gmtime, strftime

from src.custom_logging import log
from logging import Logger

from src.database.database_structure import Stages, Initiatives, SeedList
from src.database.upsert_initatives import  upsert_initiatives_to_database
from src.database.upsert_stages import  upsert_stages_to_database

from .hys_portal_scraper import Portal_Scraper

class Initiative_Scraper(Portal_Scraper):
    def __init__(self, connection: str, wait_time: int = 30, session = None, is_test: bool = False) -> None:
        super().__init__(connection, wait_time, is_test)
        
        if session is not None:
            self.session, engine = session
        else:
            self.Session, engine = super().init_database_session()
            
        
    def scrape_all(self) -> dict:
        ids = super().seedlist_get_ids(where="`initiative_updated` is Null")
        log.info(f"Wait Time set to {self.WAIT_TIME} sec.")
        log.info(f"Scraping {len(ids)} Initiatives...")
        eta = len(ids) * self.WAIT_TIME
        log.info("ETA {}".format(time.strftime('%H:%M:%S', gmtime(eta))))
        
        not_found_items = []
        for i, initiative_id in enumerate(ids):                
            try:
                with self.Session() as sess:
                    self.scrape_ini(sess, initiative_id)
                time.sleep(self.WAIT_TIME)

            except (JSONDecodeError) as e:
                log.warning(f"WARNING: No Data Found for {initiative_id}")
                not_found_items.append(initiative_id)
                    
        log.info(f"scraped initiatives {i+1}/{len(ids)} [✔️ 🎉✨]")
        log.warn(f"{len(not_found_items)} initatives where not found.")
        return not_found_items

    def scrape_ini(self, sess, initiative_id):
        # request api data
        url = self.API_INI + str(initiative_id)
        requested_data = requests.get(url, headers=self.HEADER)
        requested_data = requested_data.text
        
        if self.TEST == True:
            with open("/Users/qbukold/Heavy_Projects/GitHub/HYS-Portal-Scraper/Portal_Scraper/test_r_data.json") as f:
                requested_data = json.load(f)
        else:
            requested_data = json.loads(requested_data)

            
        initiative_data, stage_data = self.filter_ini_r_data(r_dict = requested_data)
        initiative_data["initiative_id"] = initiative_id
                    
        # upsert initative and stage data to database
        upsert_stages_to_database(stage_data, session=sess, Stages=Stages)
        upsert_initiatives_to_database(initiative_data, session=sess, Initiatives = Initiatives)
        log.info(f"Success! Updated Database on Initiative: {initiative_id}")
        
        # update seed-list initiative_updated time
        self.update_seedlist_ini_scrape(session=sess, id=initiative_id)
        
        sess.commit()

    def filter_ini_r_data(self, r_dict : dict) -> dict:
        # 1. filter
        keys_to_extract = [ 'shortTitle', 'foreseenActType', 'reference', 'dossierSummary', 'publishedDate',
                            'initiativeStatus', 'stage', 'dg', 'receivingFeedbackStatus',
                            'betterRegulationRequirement', 'topics', 'publications']
        
        initiative_data = {key: r_dict[key] for key in keys_to_extract}
        
        # clean and save topics as string    
        initiative_data["topics"] = self.deNest_topic(initiative_data["topics"])
        
        # extract consultation stage data
        stage_data = [] # "publications" on the EC Website effectively consultation stages are there metadata
        for publicationItem in initiative_data["publications"]:
            stage_data.append(self.deNest_publication(publicationItem))
            
        del initiative_data["publications"]
        
        return initiative_data, stage_data
        
    def deNest_topic(self, topics_list : list[str]) -> str:    
        if len(topics_list) == 1:
            topics_dict = topics_list[0]
            topic = topics_dict.get('label')
        elif len(topics_list) > 1:
            xi = []  
            for topics_dict in topics_list:
                topic = topics_dict.get('label')
                xi.append(topic)
            topic = '; '.join(xi)            
        else:
            topic = None
            
        return topic

    def deNest_publication(self, single_pub : list) -> dict:   
        single_pub_metadata = {} 
        
        single_pub_metadata["stage_id"] = int(single_pub["id"])
        single_pub_metadata["type"] = str(single_pub["frontEndStage"])
        single_pub_metadata["total_feedback"] = int(single_pub["totalFeedback"])
        single_pub_metadata["published_date"] = str(single_pub["publishedDate"])
        single_pub_metadata["end_date"] = str(single_pub["endDate"])
        single_pub_metadata["receiving_feedback"] = str(single_pub["receivingFeedbackStatus"])
        single_pub_metadata["initiative_id"] = int(single_pub['groupId'])  
        
        return single_pub_metadata
    
    def update_seedlist_ini_scrape(self, session, id):
        current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        update_stmt = update(SeedList).where(SeedList.initiative_id == str(id)).values(initiative_updated=current_time)
        session.execute(update_stmt)
