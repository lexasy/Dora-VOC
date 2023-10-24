import sqlite3

sqlite_connection = sqlite3.connect('user.db')

cursor = sqlite_connection.cursor()
cursor.execute(""" CREATE TABLE IF NOT EXISTS users (
                                        name text NOT NULL,
                                        surname text NOT NULL,
                                        email text NOT NULL UNIQUE,
                                        login text NOT NULL UNIQUE,
                                        password text NOT NULL
                                    ); """)
sqlite_connection.commit()