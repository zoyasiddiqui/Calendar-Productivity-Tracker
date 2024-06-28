import sqlite3

def create_connection(file):
    """Create a database connection to file"""

    connection = None
    try:
        connection = sqlite3.connect(file)
    except Exception as e:
        print(e)
    return connection

def create_table(connection):

    try:
        cur = connection.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS Events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            startdate TEXT NOT NULL,
            enddate TEXT NOT NULL,
            UNIQUE(name, category, startdate, enddate)
        );
        """
        cur.execute(sql)
    except Exception as e:
        print("ERRORRR: ",e)

def create_event(connection, category, name, start, end):
    try:
        sql = ''' INSERT INTO Events(category, name, startdate, enddate)
                VALUES(?,?,?,?) '''
        cur = connection.cursor()
        cur.execute(sql, (category, name, start, end,))
        connection.commit()
        return cur.lastrowid
    except Exception as e:
        print("ERRORRR: ",e)
        return None
    
def get_all_by_category(connection, category):
    """Return all entries in some category"""

    sql = ''' SELECT * FROM Events where category = ? '''
    cur = connection.cursor()
    cur.execute(sql, (category,))
    rows = cur.fetchall()
    events_list = []
    for r in rows:
        events_list.append(r)

    return events_list

def get_event(connection, category, name, starttime, endtime):

    sql = ''' SELECT * FROM Events where category = ? AND name = ? AND startdate = ? AND enddate = ? '''
    cur = connection.cursor()
    cur.execute(sql, (category,name,starttime,endtime,))
    rows = cur.fetchall()
    events_list = []
    for r in rows:
        events_list.append(r)

    return events_list

def delete_event(connection, category, name, startdate, enddate):
    """Delete an event by category, name, startdate, and enddate"""
    try:

        events = get_event(connection, category, name,startdate,enddate)
        print(events)

        sql = ''' DELETE FROM Events WHERE category = ? AND name = ? AND startdate = ? AND enddate = ? '''
        cur = connection.cursor()
        cur.execute(sql, (category, name, startdate, enddate,))
        connection.commit()

        return cur.rowcount  # Returns the number of rows deleted
    except Exception as e:
        print("ERROR: ", e)
        return None

def main():
    database = "Events.db"
    conn = create_connection(database)
    if conn != None:
        create_table(conn)
    else:
        print("connection failed")

    return conn

