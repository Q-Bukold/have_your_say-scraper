import logging
from sqlalchemy.orm import sessionmaker

from src.hys_portal_scraper import Portal_Scraper
from src.initiative_scraper import Initiative_Scraper
from src.feedback_scraper import Feedback_Scraper
from src.attachment_scraper import Attachment_Scraper 

from src.seedlist_handler import SeedList_Handler


from src.database.database_connection import database_connection


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger('sqlalchemy.engine')

    con = database_connection()
    wait_time = 10
    Attachment_Scraper.scrape_all()
    
    
    
    
    #Portal_Scraper(connection = con, wait_time=5).scrape(test=True)
