from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, Boolean, BigInteger
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import declarative_base

# Define the database structure
Base = declarative_base()

class Initiatives(Base):
    __tablename__ = 'initiatives' 
    
    initiative_id = Column(Integer, primary_key=True)
    initiative_name = Column(String(250), nullable=False)
    act_type = Column(String(10), nullable=False)
    reference_document = Column(String(50))
    dossier_summary = Column(Text)
    published_date = Column(DateTime)
    initiative_status = Column(String(10))
    current_stage = Column(String(20))
    dg = Column(String(5))
    receiving_feedback = Column(String(10))
    better_regulation_requirements = Column(String(100))
    topic = Column(String(250))
    db_update = Column(DateTime)

class Stages(Base):
    __tablename__ = 'stages'  
    stage_id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)
    total_feedback = Column(Integer, nullable=False)
    published_date = Column(DateTime)
    end_date = Column(DateTime)
    receiving_feedback = Column(String(10))
    initiative_id = Column(Integer, nullable=False)
    db_update = Column(DateTime)
    
class Feedbacks(Base):
    __tablename__ = 'feedbacks'  
    feedback_id = Column(Integer, primary_key=True)
    language = Column(String(2), nullable=False)
    country = Column(String(3), nullable=False)
    organization = Column(String(300), nullable=False)
    tr_id = Column(String(250))
    feedback = Column(Text, nullable=False)  # Text is used for longer string-based data
    date_feedback = Column(DateTime)
    is_anonymous = Column(Boolean)
    user_type = Column(String(30))
    company_size = Column(String(100))
    scope = Column(String(100))
    governance_level = Column(String(100))
    hash_name = Column(BigInteger)
    stage_id = Column(Integer, nullable=False)
    db_update = Column(DateTime)

class TextFileContents(Base):
    __tablename__ = 'attachments'
    unique_id = Column(String(50), primary_key=True)
    feedback_id = Column(Integer, nullable=False)
    attachment_number = Column(Integer, nullable=False)
    stage_id = Column(Integer, nullable=False)
    content = Column(LONGTEXT, nullable=False)
    db_update = Column(DateTime)