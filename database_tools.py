import sys
from persistence import PersistenceManager
from myapp import db_connector

if __name__ == "__main__":
    if len (sys.argv) == 1:
        print("Please provide function [create|destroy|recreate]")
        exit(0)

    if sys.argv[1] == 'destroy' or sys.argv[1] == 'recreate':
        pm = PersistenceManager(db_connector)
        pm.drop_schema()
        db_connector.get_session().commit()
        db_connector.get_session().close_all()

    if sys.argv[1] == 'create' or sys.argv[1] == 'recreate':
        pm = PersistenceManager(db_connector)
        pm.create_schema()
        pm.populate_reference_tables()
        db_connector.get_session().commit()
        db_connector.get_session().close_all()
