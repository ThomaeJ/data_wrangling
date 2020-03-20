import sqlite3

sqlite_file = 'Denver.db'    

# Connect to the database
conn = sqlite3.connect(sqlite_file)

# Get a cursor object
cur = conn.cursor()

cur.execute(''' CREATE TABLE nodes(id INTEGER, lat INTEGER, lon INTEGER, user TEXT, 
                uid INTEGER, version INTEGER, changeset TEXT, timestamp TEXT) ''')
cur.execute(''' CREATE TABLE nodes_tags(id INTEGER, key INTEGER, value TEXT, type TEXT) ''')
cur.execute(''' CREATE TABLE ways(id INTEGER, user TEXT, uid INTEGER, version INTEGER, changeset TEXT, timestamp TEXT) ''')
cur.execute(''' CREATE TABLE ways_nodes(id INTEGER, node_id INTEGER, position INTEGER) ''')
cur.execute(''' CREATE TABLE ways_tags(id INTEGER, key INTEGER, value TEXT, type TEXT) ''')

# commit the changes
conn.commit()

#These functions read data from each individual csv file to populate each individual table
with open('nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'].decode("utf-8"), i['lat'].decode("utf-8"), i['lon'].decode("utf-8"), i['user'].decode("utf-8"),
             i['uid'].decode("utf-8"), i['version'].decode("utf-8"), i['changeset'].decode("utf-8"), 
              i['timestamp'].decode("utf-8")) for i in dr]

#Each of these commands actually insert our values into table and columns    
cur.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db)

with open('nodes_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'].decode("utf-8"), i['key'].decode("utf-8"), i['value'].decode("utf-8"), 
              i['type'].decode("utf-8")) for i in dr]

cur.executemany("INSERT INTO nodes_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db)

with open('ways.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'].decode("utf-8"), i['user'].decode("utf-8"), i['uid'].decode("utf-8"), i['version'].decode("utf-8"),
             i['changeset'].decode("utf-8"), i['timestamp'].decode("utf-8")) for i in dr]
    
cur.executemany("INSERT INTO ways(id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db)

with open('ways_nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'].decode("utf-8"), i['node_id'].decode("utf-8"), i['position'].decode("utf-8")) for i in dr]
    
cur.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db)  

with open('ways_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'].decode("utf-8"), i['key'].decode("utf-8"), i['value'].decode("utf-8"), 
              i['type'].decode("utf-8")) for i in dr]

cur.executemany("INSERT INTO ways_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db)

#saving our changes
conn.commit()

#Each function below represents an SQL query we will use to get information from the database
def number_of_nodes():
    result = cur.execute('SELECT COUNT(*) FROM nodes')
    return result.fetchone()[0]

def number_of_ways():
    result = cur.execute('SELECT COUNT(*) FROM ways')
    return result.fetchone()[0]

def number_of_unique_users():
    result = cur.execute('SELECT COUNT(distinct(uid)) FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways)')
    return result.fetchone()[0]

def single_time_users():
    result = cur.execute('SELECT COUNT(*) FROM (SELECT k.user, COUNT(*) as num FROM (SELECT user 
                         FROM nodes UNION ALL SELECT user FROM ways) as k GROUP BY k.user HAVING num=1);')
    return result.fetchone()[0]

def number_of_hydrants():
    result = cur.execute('SELECT COUNT(*) FROM nodes_tags WHERE value == ("fire_hydrant" or "hydrant")')
    return result.fetchone()[0]

def predominate_religion():
    result = cur.execute('SELECT value, COUNT(value) FROM nodes_tags WHERE key == "religion" 
                         GROUP BY value ORDER BY 2 DESC LIMIT 1')
    return result.fetchone()[0]
	
#Calling each fuction from above to see our results	
print "Number of nodes: " ,number_of_nodes()
print "Number of ways: " ,number_of_ways()
print "Number of unique users: " ,number_of_unique_users()
print "Number of one-time contributors: " ,single_time_users()
print "Number of Tracked Denver Fire Hydrants: " ,number_of_hydrants()
print "Religion with the most locations: " ,predominate_religion()
