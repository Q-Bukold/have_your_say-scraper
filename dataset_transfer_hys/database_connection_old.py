

def database_connection():
    user = "root"
    password = "Sql2002!"
    host = "localhost"
    port = "3306"
    database = "hysPortal"
    
    return f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

'''
def database_connection():
    user = "u546836483_qbukold"
    password = "Mysql2002!"
    host = "srv927.hstgr.io"
    port = "3306"
    database = "u546836483_Test_Database"
    
    return f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

'''