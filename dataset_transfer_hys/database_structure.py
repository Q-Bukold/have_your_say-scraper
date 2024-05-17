from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, Boolean, BigInteger, BINARY
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

class Stages(Base):
    __tablename__ = 'stages'
    id = Column(String(100), primary_key=True)
    stage_id = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    total_feedback = Column(Integer, nullable=False)
    published_date = Column(DateTime)
    end_date = Column(DateTime)
    receiving_feedback = Column(String(10))
    initiative_id = Column(Integer, nullable=False)
    feedback_updated = Column(DateTime)
    attachment_updated = Column(DateTime)
    
class Feedbacks(Base):
    __tablename__ = 'feedbacks'  
    id = Column(String(100), primary_key=True)
    feedback_id = Column(Integer, nullable=False)
    language = Column(String(2), nullable=False)
    country = Column(String(3))
    organization = Column(String(300))
    tr_id = Column(String(250))
    feedback = Column(Text, nullable=False)  # Text is used for longer string-based data
    date_feedback = Column(DateTime)
    is_anonymous = Column(Boolean)
    user_type = Column(String(30))
    company_size = Column(String(100))
    scope = Column(String(100))
    governance_level = Column(String(100))
    hashed_name = Column(BigInteger)
    stage_id = Column(Integer, nullable=False)
    attachments = Column(Integer, nullable=False)

class Attachments(Base):
    __tablename__ = 'attachments'
    document_id = Column(String(100), primary_key=True)
    attachment_id = Column(Integer, nullable=False)
    feedback_id = Column(Integer, nullable=False)
    stage_id = Column(Integer, nullable=False)
    content = Column(LONGTEXT)
    file = Column(String(250))

class SeedList(Base):
    __tablename__ = 'seed_list'
    initiative_id = Column(Integer, primary_key=True)
    initiative_name = Column(String(250), nullable=False)
    seed_list_updated = Column(DateTime)
    initiative_updated = Column(DateTime)
