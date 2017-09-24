#!/usr/bin/python3
import subprocess
import threading
import time
from platform import system as system_name  # System/OS name
from sqlite3 import Error, sqlite3


def create_connection(db_file):
    """ Create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        return sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return None


def run_statement(conn, sql):
    """ Run SQL statement
    :param conn: Connection object
    :param sql: A SQL statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)


def create_table(conn):
    create_table_sql = """CREATE TABLE
            IF NOT EXISTS ping (
                id INTEGER PRIMARY KEY,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                latency REAL,
                dest_ip TEXT,
                timeout INTEGER(1),
                had_no_route INTEGER(1)
            );"""
    run_statement(conn, create_table_sql)


def add_ping_result(conn, ping):
    """
       Insert a new ping record into the pings table
       :param conn:
       :param ping:
       :return: project id
       """
    sql = ''' INSERT INTO ping(latency, dest_ip, timeout, had_no_route) VALUES(?,?,?,?) '''
    cur = conn.cursor()
    try:
        cur.execute(sql, ping)
        conn.commit()
    except Error as e:
        print(e)
    return cur.lastrowid


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that some hosts may not respond to a ping request even if the host name is valid.
    """
    parameters = "-n 1" if system_name().lower() == "windows" else "-c 1"
    cmd = subprocess.Popen("ping " + parameters + " " + host, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    throwaway = cmd.stdout.readline()
    err = cmd.stderr.readline().decode('UTF-8').strip()
    line = cmd.stdout.readline().decode('UTF-8').strip()
    latency = 0
    timeout = 0
    had_no_route = 0
    if len(err) > 0:
        if "Request timeout" in err:
            timeout = 1
        if "No route to host" in err or "Destination Host Unreachable" in err:
            had_no_route = 1
    if "time=" in line:
        latency = line.split(" ")[-2][5:]
    if timeout == 0.0 and latency == 0 and had_no_route == 0:
        timeout = 1
    return latency, host, timeout, had_no_route


def main():
    database = "./sqlite.db"
    while True:
        for ip in ["10.13.37.1", "8.8.8.8"]:
            threading.Thread(target=threaded_ping, args=(database, ip)).start()
            time.sleep(15)
            # thread.join()
            # print("thread finished for ip", ip)


def threaded_ping(database, ip):
    print("Running thread for ip", ip)
    conn = create_connection(database)
    if conn is not None:
        create_table(conn)
        # todo add smart retries if ip starts failing
        add_ping_result(conn, ping(ip))
        conn.close()
        print("Finished thread for ip", ip)
    else:
        print("Error! cannot create the database connection.")


if __name__ == '__main__':
    main()
