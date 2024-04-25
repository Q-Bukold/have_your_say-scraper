import pandas as pd
from typing import Type
from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime
from tqdm.notebook import tqdm
import os

from datetime import datetime

from src.database.database_structure import Stages
from src.database.parse_date_helper import parse_date


##### STAGES #####
def upsert_stages_to_database(stages : list, session, Stages = Stages):
    '''
    INSERT INTO my_table (id, data) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE data = VALUES(data), status = %s
    '''
    for stage_dict in stages:
        # Convert date columns to datetime objects or None        
        stage_dict["end_date"] = parse_date(stage_dict["end_date"])
        stage_dict["published_date"] = parse_date(stage_dict["published_date"])

        insert_stmt = insert(Stages).values(
                                        id                  = str(stage_dict["initiative_id"]) + "_" + str(stage_dict["stage_id"]),
                                        stage_id            = stage_dict["stage_id"],
                                        type                = stage_dict["type"],
                                        total_feedback      = stage_dict["total_feedback"],
                                        published_date      = stage_dict["published_date"],
                                        end_date            = stage_dict["end_date"],
                                        receiving_feedback  = stage_dict["receiving_feedback"],
                                        initiative_id       = stage_dict["initiative_id"],
                                                    )
            
        #print(insert_stmt.inserted)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(receiving_feedback=insert_stmt.inserted.receiving_feedback,
                                                                    published_date=insert_stmt.inserted.published_date,
                                                                    end_date=insert_stmt.inserted.end_date
                                                                        )
        #print(f"\n{on_duplicate_key_stmt}\n")
        session.execute(on_duplicate_key_stmt)
    
    # Commit the session to save records to database
    #session.commit()
            
    #session.close()
    return None
