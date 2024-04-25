import pandas as pd
from typing import Type
from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime
from tqdm.notebook import tqdm
import os

##### FEEDBACKS #####
def upsert_feedbacks_to_database(feedback_dict : dict, session = None, Feedbacks = None):
    '''
    INSERT INTO my_table (id, data) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE data = VALUES(data), status = %s
    '''

    insert_stmt = insert(Feedbacks).values(
                                            feedback_id = feedback_dict["id"]
                                            language = feedback_dict["language"]
                                            country = feedback_dict["country"]
                                            organization = feedback_dict["organization"]
                                            tr_id = feedback_dict[""]
                                            feedback = feedback_dict["feedback"]
                                            date_feedback = feedback_dict[""]
                                            is_anonymous = feedback_dict[""]
                                            user_type = feedback_dict[""]
                                            company_size = feedback_dict[""]
                                            scope = feedback_dict[""]
                                            governance_level = feedback_dict[""]
                                            hash_name = feedback_dict[""]
                                            stage_id = feedback_dict[""]
                                            attachments = feedback_dict["attachments"]
                                            )
    
    #print(insert_stmt.inserted)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(feedback=insert_stmt.inserted.feedback,
                                                                db_update = insert_stmt.inserted.db_update
                                                                #status='U'
                                                                )
    #print(f"\n{on_duplicate_key_stmt}\n")
    session.execute(on_duplicate_key_stmt)
    
    # Commit the session to save records to database
    #session.commit()
        

    #session.close()
    return None
