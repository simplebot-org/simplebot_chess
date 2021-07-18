from contextlib import contextmanager
from threading import Lock

from sqlalchemy import Column, Integer, String, create_engine  # type: ignore
from sqlalchemy.ext.declarative import declarative_base, declared_attr  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore


class Base:
    @declared_attr
    def __tablename__(cls):  # noqa
        return cls.__name__.lower()  # noqa


Base = declarative_base(cls=Base)  # type: ignore
_Session = sessionmaker()
_lock = Lock()


class Game(Base):
    p1 = Column(String(500), primary_key=True)
    p2 = Column(String(500), primary_key=True)
    chat_id = Column(Integer, nullable=False)
    board = Column(String)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    with _lock:
        session = _Session()
        try:
            yield session
            session.commit()  # noqa
        except:  # noqa
            session.rollback()  # noqa
            raise
        finally:
            session.close()  # noqa


def init(path: str, debug: bool = False) -> None:
    """Initialize engine."""
    engine = create_engine(path, echo=debug)
    Base.metadata.create_all(engine)  # type: ignore
    _Session.configure(bind=engine)
