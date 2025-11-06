"""
Script para inicializar la base de datos
Ejecutar: python init_db.py
"""
from database import engine, Base
from models import Turno

def init_database():
    """
    Crea todas las tablas en la base de datos
    """
    print("🔧 Inicializando base de datos...")
    print(f"📊 Database URL: {engine.url}")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente!")
        
        # Mostrar las tablas creadas
        print("\n📋 Tablas en la base de datos:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
        
        print("\n✨ Base de datos lista para usar!")
        
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        raise

if __name__ == "__main__":
    init_database()
