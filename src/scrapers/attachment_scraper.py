import time
import requests

from sqlalchemy import update
from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime

from src.helpers.custom_logging import log
from src.database.database_structure import Stages, Attachments, Feedbacks
from ..hys_portal_scraper import Portal_Scraper

# for pdf to txt conversion
import multiprocessing
import os
import fitz
import time
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm
from src.pdf_to_txt.clean_extract import convert_attachments_to_txt, extract_text_from_pdf

class Attachment_Scraper(Portal_Scraper):
    def __init__(self, connection: str, wait_time: int = 30, document_id : str = None) -> None:
        super().__init__(connection, wait_time)
    
        self.Session, self.engine = super().init_database_session()
        self.WAIT_TIME = wait_time
        
        self.document_id = document_id
    
    def scrape_all(self):
        ids = super().attachments_get_ids(where="`content` is Null")
        
        not_found_items = []
        for i, document_id in enumerate(ids):
            log.info(f"Scraping Document with ID {document_id}")
            self.document_id = str(document_id)
            
            self.scrape_attachments()
            
            self.engine.dispose()
    
    def scrape_all_of_stage(self, stage_id):
        ids = super().attachments_get_ids(where=f"`content` is Null AND `stage_id` = {stage_id}")
        log.info(f"Scraping Documents of stage ID {stage_id}")
        
        not_found_items = []
        for i, document_id in enumerate(ids):
            log.info(f"Scraping Document with ID {document_id}")
            self.document_id = str(document_id)
            
            self.scrape_attachments()
            
            self.engine.dispose()
                

    def scrape_attachments(self):
        with self.Session() as self.sess:
            url = self.API_ATTACHMENTS + str(self.document_id)
            print(url)
            self.TARGET = "tmp/tmp.pdf"
            self._get_file(url=url)
            text = self.convert_pdf_to_txt()
            self._upsert_text_content_to_db(text)
            time.sleep(self.WAIT_TIME)
            
            self._insert_file_url_to_db(url)
            self.sess.commit()

    # function copied in part from felix rech hys_scraper
    def _get_file(self, url: str) -> None:
        """Download a (binary) file to given location.

        Parameters
        ----------
        url : str
            URL of the file to download.
        target : str
            Name of the file to save into.
        """
        pdf = requests.get(url, stream=True)
        with open(self.TARGET, "wb") as f:
            for chunk in pdf.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    
    def convert_pdf_to_txt(self):
        output = extract_text_from_pdf(self.TARGET)        
        return output


    def _insert_file_url_to_db(self, url):
        insert_stmt = update(Attachments).where(Attachments.document_id == self.document_id).values(file=url)
        self.sess.execute(insert_stmt)
        pass
    
    def _upsert_text_content_to_db(self, text):
        insert_stmt = update(Attachments).where(Attachments.document_id == self.document_id).values(content=text)
        self.sess.execute(insert_stmt)
        
    