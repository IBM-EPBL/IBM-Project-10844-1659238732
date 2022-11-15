import ibm_db
from config import DB2_CONNECTION_STR

print("Connecting to IBM DB2...")
dbConn = ibm_db.pconnect(DB2_CONNECTION_STR, "", "")
print("Connected to IBM DB2")

def select(query, params=None):
    try:
        stmt = ibm_db.prepare(dbConn, query)
        if (params == None):
            ibm_db.execute(stmt)
        else:
            params = tuple(params)
            ibm_db.execute(stmt, params)
        row = ibm_db.fetch_assoc(stmt)
        data = []
        while (row):
            data.append(row)
            row = ibm_db.fetch_assoc(stmt)
        return data
    except:
        return False


def insert(query, params):
    try:
        if (params != None):
            params = tuple(params)
        stmt = ibm_db.prepare(dbConn, query)
        ibm_db.execute(stmt, params)
        return True
    except:
        return False


def update(query, params):
    try:
        if (params != None):
            params = tuple(params)
        stmt = ibm_db.prepare(dbConn, query)
        ibm_db.execute(stmt, params)
        return True
    except:
        return False


def delete(query, params):
    try:
        if (params != None):
            params = tuple(params)
        stmt = ibm_db.prepare(dbConn, query)
        ibm_db.execute(stmt, params)
        return True
    except:
        return False
