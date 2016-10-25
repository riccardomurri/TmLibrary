import os

import sqlalchemy
import pytest

from tmlib.models import Model
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope='session')
def config(tmpdir_factory):
    """Session-wide test `Flask` application."""

    cfg = {}
    cfg['TMAPS_STORAGE'] = str(tmpdir_factory.mktemp('experiments'))
    if 'TMAPS_DB_URI' not in os.environ:
        raise Exception(
            'No URI to the testing db found in the environment. '
            'To set it issue the command:\n'
            '    $ export TMAPS_DB_URI=postgresql://{user}:{password}@{host}:5432/tissuemaps_test'
        )
    else:
        cfg['POSTGRES_DATABASE_URI'] = os.environ['TMAPS_DB_URI']

    return cfg


@pytest.yield_fixture(scope='session', autouse=True)
def engine(config, request):

    engine = sqlalchemy.create_engine(config['POSTGRES_DATABASE_URI'])

    Model.metadata.drop_all(engine)
    Model.metadata.create_all(engine)

    try:
        yield engine
    finally:
        Model.metadata.drop_all(engine)
        engine.dispose()


@pytest.yield_fixture(scope='session')
def Session(engine):
    smaker = sessionmaker(bind=engine)

    try:
        yield smaker
    finally:
        smaker.close_all()


@pytest.yield_fixture(scope='function')
def session(Session):
    session = Session()
    session.begin_nested()

    try:
        yield session
    finally:
        session.rollback()


@pytest.yield_fixture(scope='session')
def persistent_session(Session, request):
    session = Session()

    try:
        yield session
    finally:
        session.rollback()