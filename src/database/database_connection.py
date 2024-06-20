def database_connection():
    user = "u546836483_bukold"
    password = "Mysql2002!"
    host = "191.96.63.52"
    port = "3306"
    database = "u546836483_hysPortal"
    
    return f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

