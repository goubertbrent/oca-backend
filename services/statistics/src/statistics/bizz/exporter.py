import hashlib
import logging

import sqlalchemy
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text, Integer, Date
from statistics.consts import db_user, db_pass, db_name,\
    cloud_sql_connection_name, db_table_name
from statistics.models.stats import StatsExportDaily


url = URL(
    drivername='postgres+pg8000',
    username=db_user,
    password=db_pass,
    database=db_name,
    query={
        'unix_sock': '/cloudsql/{}/.s.PGSQL.5432'.format(
            cloud_sql_connection_name)
    }
)
engine = sqlalchemy.create_engine(url)
base = declarative_base()

class ServiceTagUsage(base):  
    __tablename__ = db_table_name

    uid = Column(Text, primary_key=True)
    d = Column(Date)
    service = Column(Text)
    app_id = Column(Text)
    tag = Column(Text)
    amount = Column(Integer)


def create_uid(items):
    digester = hashlib.sha256()
    for i in items:
        v = i.encode('utf8') if isinstance(i, unicode) else i
        digester.update(v)
    return digester.hexdigest().upper()


def export_day(service_user, day):
    logging.debug("export_day: %s", day)
    session = sessionmaker(engine)()
    try:
        service_parent_key = StatsExportDaily.create_service_parent_key(service_user)
        qry = StatsExportDaily.query(ancestor=service_parent_key).filter(StatsExportDaily.date == day)
        for m in qry:
            service_id = '%s/%s' % (m.service_user_email, m.service_identity)
            for app_stats in m.app_stats:
                for data in app_stats.data:
                    item = ServiceTagUsage(uid=create_uid([str(m.date), service_id, app_stats.app_id, data.tag]),
                                           d=m.date,
                                           service=service_id,
                                           app_id=app_stats.app_id,
                                           tag=data.tag,
                                           amount=data.count)
                    session.add(item)
        
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

