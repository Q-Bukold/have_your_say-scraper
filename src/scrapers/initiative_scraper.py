import requests
import json
from json import JSONDecodeError
from typing import List

from sqlalchemy import update
import time
from time import gmtime, strftime

from src.helpers.custom_logging import log

from src.database.database_structure import Stages, Initiatives, SeedList
from src.database.upsert_initatives import  upsert_initiatives_to_database
from src.database.upsert_stages import  upsert_stages_to_database

from ..hys_portal_scraper import Portal_Scraper

class Initiative_Scraper(Portal_Scraper):
    def __init__(self, connection: str, wait_time: int = 30) -> None:
        super().__init__(connection, wait_time)
        

        self.Session, engine = super().init_database_session()
            
        
    def scrape_all(self) -> dict:
        """Scrapes all Initatives where `initiative_updated` Value in Seedlist Table is Null"

        """

        ids = super().seedlist_get_ids(where="`initiative_updated` is Null")
        log.info(f"Wait Time set to {self.WAIT_TIME} sec.")
        log.info(f"Scraping {len(ids)} Initiatives...")
        eta = len(ids) * self.WAIT_TIME
        log.info("ETA {}".format(time.strftime('%H:%M:%S', gmtime(eta))))
        
        not_found_items = []
        for i, initiative_id in enumerate(ids):                
            try:
                with self.Session() as sess:
                    self.scrape_ini(session_instance=sess, initiative_id=initiative_id)
                self.engine.dispose()
                time.sleep(self.WAIT_TIME)

            except (JSONDecodeError) as e:
                log.warning(f"WARNING: No Data Found for {initiative_id}")
                not_found_items.append(initiative_id)
                    
        log.info(f"scraped initiatives {i+1}/{len(ids)} [✔️ 🎉✨]")
        log.warn(f"{len(not_found_items)} initatives where not found.")
        return not_found_items

    def scrape_ini(self, session_instance, initiative_id):
        """Scrape the Initiative's Metadata and Metadata of all associated Consultations Stages.
        Saves all data in database.
        
        Parameters
        ----------
        sess : sqlalchemy session instance
        
        initiative_id : str
            ID of an Initataive
        """
        # request api data
        url = self.API_INI + str(initiative_id)
        requested_data = requests.get(url, headers=self.HEADER)
        requested_data = requested_data.text
        
        requested_data = json.loads(requested_data)

            
        initiative_data, stage_data = self.filter_ini_r_data(r_dict = requested_data)
        initiative_data["initiative_id"] = initiative_id
                    
        # upsert initative and stage data to database
        upsert_stages_to_database(stage_data, session=session_instance, Stages=Stages)
        upsert_initiatives_to_database(initiative_data, session=session_instance, Initiatives = Initiatives)
        log.info(f"Success! Updated Database on Initiative: {initiative_id}")
        
        # update seed-list initiative_updated time
        self.update_seedlist_ini_scrape(session=session_instance, id=initiative_id)
        
        session_instance.commit()

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
        
    def deNest_topic(self, topics_list : List[str]) -> str:    
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
