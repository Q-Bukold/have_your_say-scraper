import logging
from sqlalchemy.orm import sessionmaker

#from src.hys_portal_scraper import Portal_Scraper
#from src.scrapers.initiative_scraper import Initiative_Scraper
from src.scrapers.feedback_scraper import Feedback_Scraper
from src.scrapers.attachment_scraper import Attachment_Scraper

#from src.database.seedlist_handler import SeedList_Handler

from src.database.database_connection import database_connection

    



if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger("sqlalchemy.engine")

    con = database_connection()
    Feedback_Scraper(connection=con, wait_time=10, stage_id="32232670").scrape_feedback() # wait_time = time between requests
    
