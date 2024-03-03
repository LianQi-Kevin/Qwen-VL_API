from sqlalchemy import Column, String, DateTime, create_engine, Integer
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.orm import sessionmaker

DATABASE_PATH = "./file_records.db"
Base = declarative_base()


class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    bytes = Column(Integer, index=True)
    purpose = Column(String, index=True)
    created_at = Column(DateTime, index=True)

    expiration = Column(DateTime, index=True)


def get_db() -> Session:
    """
    Get the session for the database.
    :returns: A new SQLAlchemy session.
    """
    engine = create_engine(f"sqlite:///{DATABASE_PATH}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
