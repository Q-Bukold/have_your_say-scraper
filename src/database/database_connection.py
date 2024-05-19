def database_connection():
    user = "USERNAME"
    password = "PASSWORD"
    host = "HOST-IP"
    port = "3306"
    database = "DATABASE_NAME"
    
    return f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

