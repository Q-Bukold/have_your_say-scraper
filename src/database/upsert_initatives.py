import pandas as pd
from typing import Type
from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime
from tqdm.notebook import tqdm
import os

from src.database.parse_date_helper import parse_date

##### INITATIVES #####
def upsert_initiatives_to_database(ini_dict : dict, session = None, Initiatives = None):
    '''
    INSERT INTO my_table (id, data) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE data = VALUES(data), status = %s
    '''
    
    if ini_dict["betterRegulationRequirement"] == [] or ini_dict["betterRegulationRequirement"]=="None":
        ini_dict["betterRegulationRequirement"] =  None
    else:
        ini_dict["betterRegulationRequirement"] = "; ".join(ini_dict["betterRegulationRequirement"])
        
    
    ini_dict["publishedDate"] = parse_date(ini_dict["publishedDate"])
    
    insert_stmt = insert(Initiatives).values(
                                        initiative_id       =               ini_dict["initiative_id"],
                                        initiative_name     =               ini_dict["shortTitle"],
                                        act_type            =               ini_dict["foreseenActType"],
                                        reference_document  =               ini_dict["reference"],
                                        dossier_summary     =               ini_dict["dossierSummary"],
                                        published_date      =               ini_dict["publishedDate"],
                                        initiative_status   =               ini_dict["initiativeStatus"],
                                        current_stage       =               ini_dict["stage"],
                                        dg                  =               ini_dict["dg"],
                                        receiving_feedback  =               ini_dict["receivingFeedbackStatus"],
                                        better_regulation_requirements =    ini_dict["betterRegulationRequirement"],
                                        topic               =               ini_dict["topics"],
                                                )




    #print(insert_stmt.inserted)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(current_stage=insert_stmt.inserted.current_stage,
                                                                better_regulation_requirements = insert_stmt.inserted.better_regulation_requirements
                                                                )
    #print(f"\n{on_duplicate_key_stmt}\n")
    session.execute(on_duplicate_key_stmt)
    
    # Commit the session to save records to database
    #session.commit()
            

    #session.close()
    return None
