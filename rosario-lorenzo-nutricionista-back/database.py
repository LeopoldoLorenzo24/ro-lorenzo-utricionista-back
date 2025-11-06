"""
Configuración de la base de datos PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL de conexión a PostgreSQL
# En producción (Render), esto vendrá de la variable de entorno DATABASE_URL
# En desarrollo local, puedes usar SQLite temporalmente
DATABASE_URL = os.getenv("DATABASE_URL")

# Render usa "postgres://" pero SQLAlchemy 1.4+ requiere "postgresql://"
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Si no hay DATABASE_URL, usar SQLite para desarrollo local
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./turnos.db"
    print("⚠️  [WARNING] Usando SQLite para desarrollo local")
else:
    print(f"✅ [INFO] Conectando a PostgreSQL")

# Crear engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=300,    # Recicla conexiones cada 5 minutos
)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependency para obtener la sesión de DB
def get_db():
    """
    Generador que proporciona una sesión de base de datos
    y la cierra automáticamente al terminar
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
