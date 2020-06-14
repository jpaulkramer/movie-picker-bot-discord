import psycopg2
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

def addrecord(key, title, submitter, votes=1):
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

    # to avoid case conflicts, set everything to lower
    title = title.lower()

    engine = sqldb.create_engine(engine_name)
    with engine.connect() as connection:
        try:
            raw_query = "INSERT INTO {} (ID, Title, Votes, Submitter) VALUES ('{}','{}',{},'{}');"
            ins_query = raw_query.format(movie_table, key, title, votes, submitter)
            connection.execute(ins_query)

        except Exception as error:
            print("Error while inserting record", error)

        finally: 
            connection.close()
            engine.dispose()
    return


def selectrecords(conn, table, where=''):
    """
    selects records from the postgres connection and returns as an array
    :param conn: postgres connection
    :param table: table to select from
    :param where: free-form where statement string tacked on end of select ex. select * from table (where x = y)
    :return: array of select statement results
    """
    try:
        cursor = conn.cursor()
        sel_query = 'SELECT * FROM {} {})'.format(table, where)
        cursor.execute(sel_query)
        data = cursor.fetchall()
    except Exception as error:
        print("Error while selecting records", error)
    return data


def updaterecord(conn, table, field, condition, value):
    """
    updates records with specified conditions.
    :param conn: postgres connection
    :param table: table to update
    :param field: field to update
    :param condition: (string) conditions, probably keyfield = key
    :param value: value to update
    :return: none
    """
    try:
        cursor = conn.cursor()
        update_query = 'UPDATE {} SET {} = {} where {} '.format(table, field, value, condition)
        cursor.execute(update_query)

    except Exception as error:
        print("Error while updating records", error)
    return


def deleterecords(conn, table, condition):
    """
    deletes records with specified condition.
    :param conn: postgres connection
    :param table: table to update
    :param condition: (string) conditions "where"
    :return: none
    """
    try:
        cursor = conn.cursor()
        delete_query = 'DELETE FROM {} where {} '.format(table, condition)
        cursor.execute(delete_query)

    except Exception as error:
        print("Error while updating records", error)
    return
