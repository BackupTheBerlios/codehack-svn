
# SQLite SQL queries for 
# initialization of contest database
#
# "INTEGER PRIMARY KEY" implies Auto-Increment
#
# ISSUES - thread safety - is appropriate for twisted adapi?

# type = 0(team), 1(judge), 2(admin)
CREATE TABLE users 
(
    id INTEGER PRIMARY KEY,
    userid TEXT UNIQUE,
    passwd TEXT,
    name TEXT UNIQUE,
    emailid TEXT,
    type INTEGER,
    score
);

# problem, result refer to index number in current contest profile
CREATE TABLE submissions 
(
    id INTEGER PRIMARY KEY,
    users_id INTEGER,
    problem INTEGER,
    language TEXT,
    ts INTEGER UNIQUE,
    result INTEGER
);

# if new is 1, then the query is unanswered, i.e is not parent for any other
CREATE TABLE queries
(
    id INTEGER PRIMARY KEY,
    parent_query_id INTEGER,
    users_id INTEGER,
    problem INTEGER,
    ts INTEGER UNIQUE,
    result INTEGER,
    new INTEGER
);
