from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine('sqlite:///your_database.db')
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

class CRUD:
    def __init__(self, model):
        self.model = model

    def create(self, **kwargs):
        session = Session()
        instance = self.model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

    def read(self, id):
        session = Session()
        instance = session.query(self.model).filter_by(id=id).first()
        return instance

    def update(self, id, **kwargs):
        session = Session()
        instance = session.query(self.model).filter_by(id=id).first()
        if instance:
            for attr, value in kwargs.items():
                setattr(instance, attr, value)
            session.commit()
            return instance
        return None

    def delete(self, id):
        session = Session()
        instance = session.query(self.model).filter_by(id=id).first()
        if instance:
            session.delete(instance)
            session.commit()
            return True
        return False
