from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from core.settings import settings

engine = create_engine(
    f'postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DB}',
    echo=True)
session_factory = sessionmaker(bind=engine)
scoped_session = scoped_session(session_factory)


class CRUD:
    def __init__(self, model):
        self.model = model
        self.scoped_session = scoped_session

    def create(self, **kwargs):
        with self.scoped_session.begin():
            instance = self.model(**kwargs)
            self.scoped_session.add(instance)
        return instance

    def read(self, id):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(id=id).first()
        return instance

    def update(self, id, **kwargs):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(id=id).first()
            if instance:
                for attr, value in kwargs.items():
                    setattr(instance, attr, value)
                return instance
        return None

    def delete(self, id):
        with self.scoped_session.begin():
            instance = self.scoped_session.query(self.model).filter_by(id=id).first()
            if instance:
                self.scoped_session.delete(instance)
                return True
        return False
