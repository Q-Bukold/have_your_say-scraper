import pandas as pd
from typing import Type
from sqlalchemy.dialects.mysql import insert
from time import gmtime, strftime
from tqdm.notebook import tqdm
import os

#### ATTACHMENTS ####
def upsert_attachments_to_database(attachment_paths : list[str], session = None, TextFileContents = None):
    
    for path_to_txt_files in tqdm(attachment_paths, total=len(attachment_paths)):
    # Iterate over the .txt files in the directory
        try:
            for filename in os.listdir(path_to_txt_files):
                if filename.endswith('.txt'):
                    file_path = os.path.join(path_to_txt_files, filename)
                    metadata = create_attachment_metadata(filename, file_path)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        metadata["content"] = file.read()
                    
                    insert_stmt = insert(TextFileContents).values(
                                            unique_id = metadata["unique_id"],
                                            feedback_id = metadata["feedback_id"],
                                            attachment_number = metadata["attachment_number"],
                                            stage_id = metadata["stage_id"],
                                            content = metadata["content"],
                                            db_update = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                                            )
                    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(db_update = insert_stmt.inserted.db_update,
                                                                                content = insert_stmt.inserted.content
                                                                                )
                    
                    session.execute(on_duplicate_key_stmt)
                    #session.commit()

        except (FileNotFoundError):
            print(f"no attachments found: {path_to_txt_files}")
            
    #session.close() 
    return None

def create_attachment_metadata(filename, file_path) -> dict:
    '''
    Creating multiple identificators from filepath and filename.
    
    filepath = .../{stage_id}/attachments/{feedback_id}_{attachment_number}.txt 
    -> attachment_nr only if multiple attachments under one feedback_id
    
    '''
    
    filename = filename.split(".")[0]
    
    stage_id = file_path.split("/")[-3]
    xi = filename.split(".")[0]
    feedback_id = xi.split("_")[0]
    
    # Split is nessesary, because according  to HYS_Scraper, the filename is 
    # "id.pdf" and "id_2.pdf", "id_3.pdf" for multiple attachments
    try:
        attachment_number = xi.split("_")[1]
    except IndexError as e:
        attachment_number = "1"
    unique_id = stage_id + "_" + feedback_id + "_" + attachment_number
    
    metadata = {}
    metadata["filename"] = filename
    metadata["stage_id"] = int(stage_id)
    metadata["feedback_id"] = int(feedback_id)
    metadata["attachment_number"] = int(attachment_number)
    metadata["unique_id"] = str(unique_id)
    
    return metadata