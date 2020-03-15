from persistence import PersistenceManager
from myapp import db_connector

if __name__ == "__main__":
    pm = PersistenceManager(db_connector)
    pm.create_schema()
    pm.populate_reference_tables()
    db_connector.get_session().commit()
    db_connector.get_session().close_all()
