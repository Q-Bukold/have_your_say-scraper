def database_connection():
    user = "u546836483_bukold"
    password = "hysPortal2024!"
    host = "srv927.hstgr.io"
    port = "3306"
    database = "u546836483_hysPortal"
    
    return f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

