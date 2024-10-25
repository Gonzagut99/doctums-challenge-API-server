from sqlmodel import SQLModel, create_engine

sql_file_name = 'database.sqlite'
sqllite_url = f'sqlite:///{sql_file_name}'

engine = create_engine(sqllite_url, echo=True)

# Aqui traemos los modelos de sqlModel, 
# para los cuales ya no se ncesita esquemas y modelos por separado.
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)