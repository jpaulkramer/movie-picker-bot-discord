import psycopg2
from datetime import datetime
import sqlalchemy as sqldb
from dotenv import load_dotenv
import os

load_dotenv()
engine_pattern = '{}://{}:{}@{}/{}'

server = 'postgresql'
user = os.getenv('POSTGRES_USER')
pw = os.getenv('POSTGRES_PASSWORD')
host = os.getenv('POSTGRES_HOSTNAME')
database = os.getenv('DATABASE_NAME')
movie_table = os.getenv('MOVIE_TABLE_NAME')

engine_name = engine_pattern.format(server,
                                    user, 
                                    pw, 
                                    host, 
                                    database)

def add_movie(key, title, submitter, votes=1):
    """
    adds record to specified table with user-specified key.
    :param conn:
    :param table:
    :param key:
    :param title:
    :param submitter:
    :param votes:
    :return:
    """

    engine = sqldb.create_engine(engine_name)
    with engine.connect() as connection:
        try:
            timestamp = datetime.now().replace(microsecond=0).isoformat().replace(':','-')
            raw_query = "INSERT INTO {} (id, title, votes, submitter, voters, timestamp) VALUES ('{}','{}',{},'{}','{}','{}');"
            ins_query = raw_query.format(movie_table, key, title, votes, submitter, f'{submitter},',timestamp)
            connection.execute(ins_query)

        except Exception as error:
            print("Error while inserting record", error)

        finally: 
            connection.close()
            engine.dispose()
    return


def get_movie_list(col=['*']):
    """
    selects records from the postgres connection and returns as an array
    :param conn: postgres connection
    :param table: table to select from
    :param where: free-form where statement string tacked on end of select ex. select * from table (where x = y)
    :return: array of select statement results
    """

    if type(col) == list:
        col = ','.join(col)
    elif not type(col) == str:
        return 

    engine = sqldb.create_engine(engine_name)
    with engine.connect() as connection:
        try:
            sel_query = f'select {col} from {movie_table}'
            resultproxy = connection.execute(sel_query)
            movie_collection = [{column: value for column, value in rowproxy.items()} for rowproxy in resultproxy]

        except Exception as error:
            print("Error while selecting records", error)
            
        finally: 
            connection.close()
            engine.dispose()

    return movie_collection


def updaterecord(table, field, condition, value):
    """
    updates records with specified conditions.
    :param conn: postgres connection
    :param table: table to update
    :param field: field to update
    :param condition: (string) conditions, probably keyfield = key
    :param value: value to update
    :return: none
    """
    
    engine = sqldb.create_engine(engine_name)
    with engine.connect() as connection:
        try:
            update_query = 'UPDATE {} SET {} = {} where {}'.format(table, field, value, condition)
            connection.execute(update_query)

        except Exception as error:
            print("Error while updating records", error)

        finally:
            connection.close()
            engine.dispose()

    return
    
def update_movie(title, field, value):
    """
    updates records with specified conditions.
    :param conn: postgres connection
    :param table: table to update
    :param field: field to update
    :param condition: (string) conditions, probably keyfield = key
    :param value: value to update
    :return: none
    """
    
    engine = sqldb.create_engine(engine_name)
    with engine.connect() as connection:
        try:
            update_query = f"UPDATE {movie_table} SET {field} = {value} where title like '{title}'"
            connection.execute(update_query)

        except Exception as error:
            print("Error while updating records", error)

        finally:
            connection.close()
            engine.dispose()

    return

def remove_movie(title):
    """
    deletes records with specified condition.
    :param conn: postgres connection
    :param table: table to update
    :param condition: (string) conditions "where"
    :return: none
    """
    engine = sqldb.create_engine(engine_name)
    with engine.connect() as connection:
        try:
            delete_query = "DELETE FROM {} where title like '{}'".format(movie_table, title)
            connection.execute(delete_query)

        except Exception as error:
            print("Error while updating records", error)
            
        finally:
            connection.close()
            engine.dispose()

    return
