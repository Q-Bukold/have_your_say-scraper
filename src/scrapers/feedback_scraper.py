from json import JSONDecodeError
import json
import time
import sys
import pandas as pd
from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime

from sqlalchemy import update

from src.helpers.custom_logging import log

from src.database.database_structure import Stages, Attachments, Feedbacks

from ..hys_portal_scraper import Portal_Scraper
from .hys_scraper import HYS_Scraper

class Feedback_Scraper(Portal_Scraper):
    def __init__(self, connection: str, stage_id : str = None, wait_time: int = 30) -> None:
        Portal_Scraper.__init__(self, connection, wait_time)  # explicit calls without super
        
        self.stage_id = stage_id
        
        self.Session, self.engine = super().init_database_session()
        self.engine.dispose()
        self.WAIT_TIME = wait_time
        
        self.current_time = gmtime()
        self.nr_of_requests = 0
        self.script_end_time = None
                
        
    def scrape_all(self):
        log.info("gmtime = {}".format(strftime("%Y-%m-%d %H:%M:%S", self.current_time)))
        ids = super().stages_get_ids()  #WHERE stages.feedback_updated in (Null, '1111-01-01 01:01:01') AND
                                        #stages.type != 'OPC_LAUNCHED' AND stages.total_feedback != 0
        
        log.info(f"Wait Time set to {self.WAIT_TIME} sec.")
        if len(ids) > 0:
            log.info(f"Scraping Feedback of {len(ids)} Stages ...\n")
        else:
            log.error(f"Scraping Feedback of {len(ids)} Stages. Not Possible.")
            return IndexError

        not_found_items = []
        for i, stage_id in enumerate(ids):   
            self.stage_id = str(stage_id)
            self.scrape_feedback()
            self.engine.dispose()
                
        
        log.info(f"scraped feedbacks of {i+1}/{len(ids)} Stages [✔️ 🎉✨]\n")
        return not_found_items

    
    def scrape_feedback(self):
        log.info(f"Scraping Stage: {self.stage_id}")
        hys = HYS_Scraper(publication_id=self.stage_id, sleep_time=self.WAIT_TIME, header=self.HEADER) #scraper already contains sleep timer
        size, n_pages = self._determine_nr_of_pages(hys)
        self.nr_of_requests += 1
                
        if n_pages == 0:
            log.info(f"No feedbacks found")
            with self.Session() as self.sess:
                self._update_seedlist_feedback_scrape()
                self.sess.commit()

        # loop through all feedback pages of stage
        elif n_pages > 0:
            eta = n_pages * self.WAIT_TIME
            log.info("ETA of Stage-Data {}".format(time.strftime('%H:%M:%S', gmtime(eta))))
            self._scrape_pages(size, n_pages, hys)
                
        return None

    def _determine_nr_of_pages(self, hys):
        # Access API to determine default page size and number of pages
        # -> following two lines taken from HYS-Scraper by felixrech
        initial = hys._scrape_page()
        size, n_pages = initial["page"]["size"], initial["page"]["totalPages"]
        
        return size, n_pages

    def _scrape_pages(self, size, n_pages, hys):
        # -> following function is inspired from HYS-Scraper by felixrech

        
        for page in range(self._remember_pageNr(), n_pages): # one page are 10 Feedbacks of an stage
            try: # scrape one page at a time. Reset from page_nr self._remember_pageNr(), if error occured       
                page_data = hys._scrape_page(page, size=size)
                self.nr_of_requests += 1
                log.info(f"Scraped Page {page+1}/{n_pages}")
                page_data = page_data["_embedded"]["feedback"]
                len_last_page = len(page_data)
                
                # upsert page to DB
                with self.Session() as self.sess:
                    self._feedbacks_to_db(page_data)
                    self.sess.commit()
                    
            except (Exception, KeyboardInterrupt) as e: # in case of error: remember last scraped page  
                log.error(e)
                self._remember_pageNr(update_page_nr=page-1)
                time_delta = time.mktime(gmtime())  -  time.mktime(self.current_time)
                log.info("Made {x} requests in {time} sec".format(x=self.nr_of_requests,
                            time=time.strftime("%H:%M:%S", time.gmtime(time_delta))))
                sys.exit(0)
        
        self._remember_pageNr(update_page_nr=n_pages-1)
        # finished all pages! update time of last scrape 
        with self.Session() as self.sess:
            self._update_seedlist_feedback_scrape()
            self.sess.commit()
            # reset
        log.info(f"Scraped {10 * (n_pages-1) + len_last_page} feedbacks\n")
        self._remember_pageNr(update_page_nr=0)
        
        return None #Data upserted to DB
    
    def _remember_pageNr(self, update_page_nr:int = 0):
        # reset or re-assign
        if update_page_nr < 0:
            update_page_nr = 0
        
        key = str(self.stage_id)
        value = update_page_nr
        current_value = 0
        
        config = json.load(open('tmp/config.json'))
        
        # check if status of stage_id already saved
        if key in config.keys():
            # get value
            current_value = config[key]
            # update value
            config[key] = update_page_nr
        else:
            config[key] = value
            
        json.dump(config, open('tmp/config.json', 'w'))

        return current_value
            
    
    # to DB
    def _feedbacks_to_db(self, feedback_page):
        for feedback in feedback_page:
            self._upsert_feedbacks_to_database(feedback)
    
    def _upsert_feedbacks_to_database(self, feedback_dict : dict):
        '''
        INSERT INTO my_table (id, data) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE data = VALUES(data), status = %s
        '''
        feedback_dict = self._structure_feedback(feedback_dict)

        insert_stmt = insert(Feedbacks).values(
                                                id          = str(feedback_dict["stage_id"]) + "_" + str(feedback_dict["feedback_id"]),
                                                feedback_id = feedback_dict["feedback_id"],
                                                language = feedback_dict["language"],
                                                country = feedback_dict["country"],
                                                organization = feedback_dict["organization"],
                                                tr_id = feedback_dict["tr_id"],
                                                feedback = feedback_dict["feedback"],
                                                date_feedback = feedback_dict["date_feedback"],
                                                is_anonymous = feedback_dict["is_anonymous"],
                                                user_type = feedback_dict["user_type"],
                                                company_size = feedback_dict["company_size"],
                                                scope = feedback_dict["scope"],
                                                governance_level = feedback_dict["governance_level"],
                                                hashed_name = feedback_dict["hashed_name"],
                                                stage_id = feedback_dict["stage_id"],
                                                attachments = feedback_dict["attachments"]
                                                )
        
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(attachments = insert_stmt.inserted.attachments)
        self.sess.execute(on_duplicate_key_stmt)
        return None

    
    def _structure_feedback(self, f) -> dict:
        
        # replace all empty strings with None
        f = {key: None if value == "" else value for key, value in f.items()}
        
        d = {}
        # change dtypes and add missing items as key : None
        d["feedback_id"]         = int(f["id"])
        
        d["country"]             = f.get("country", None)
        d["organization"]        = f.get("organization", None) #.get defaults to None if no key found
        d["tr_id"]               = f.get("tr_number", None)
        d["user_type"]           = f.get("userType", None)
        d["company_size"]        = f.get("companySize", None)
        d["scope"]               = f.get("scope", None)
        d["governance_level"]    = f.get("governance_level", None)

        # is always in feedback        
        d["language"]            = f["language"]
        d["feedback"]            = f.get("feedback", None)
        d["date_feedback"]       = f["dateFeedback"]
        d["stage_id"]            = int(self.stage_id)
        
        # hash names for privacy reasons
        f["firstName"] = f.get("firstName", None)
        f["surname"] = f.get("surname", None)
        if f["firstName"] is None and f["surname"] is None:
            d["hashed_name"]     = None
        else:
            d["hashed_name"]     = hash(str(f["firstName"] + f["surname"]))
        
        # EC misspelled Instittution, fix it.
        if d["user_type"] == "ACADEMIC_RESEARCH_INSTITTUTION":
            d["user_type"] = "ACADEMIC_RESEARCH_INSTITUTION"
        
        # save how many attachments the feedback has in dictionary and upsert the attachment metadata to Attachments Table
        list_of_attachments = f["attachments"]
        d["attachments"] = len(list_of_attachments)
        if len(list_of_attachments) == 0:
            None    
        elif len(list_of_attachments) > 0:
            for attachment in f["attachments"]:
                attachment_data = {}
                attachment_data["attachment_id"] = int(attachment["id"])
                attachment_data["document_id"] = str(attachment["documentId"])
                attachment_data["feedback_id"] = int(d["feedback_id"])
                attachment_data["stage_id"] = int(self.stage_id)
                self._upsert_attachment_data_to_database(attachment_data)
        else:
            raise ValueError
        
        # change publication Status to Boolean and rename to is_anonymous
        if f["publication"] == "WITHINFO":
            d["is_anonymous"] = False
        elif f["publication"] == "ANONYMOUS":
            d["is_anonymous"] = False
        else:
            raise ValueError
        
        return d

    def _upsert_attachment_data_to_database(self, attachment_data):
        insert_stmt = insert(Attachments).values(
                                    attachment_id = attachment_data["attachment_id"],
                                    document_id = attachment_data["document_id"],
                                    feedback_id = attachment_data["feedback_id"],
                                    stage_id = attachment_data["stage_id"]
                                                )
        
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(document_id = insert_stmt.inserted.document_id)
        self.sess.execute(on_duplicate_key_stmt)
        return None

    def _update_seedlist_feedback_scrape(self):
        update_stmt = update(Stages).where(Stages.stage_id == self.stage_id).values(feedback_updated=strftime("%Y-%m-%d %H:%M:%S", self.current_time))
        self.sess.execute(update_stmt)

        