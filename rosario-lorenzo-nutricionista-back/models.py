"""
Modelos de base de datos para el sistema de turnos
"""
from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.sql import func
from database import Base

class Turno(Base):
    """
    Modelo de turno en la base de datos
    """
    __tablename__ = "turnos"
    
    # Columnas
    id = Column(String, primary_key=True, index=True)
    estado = Column(String, nullable=False, index=True)  # pendiente_de_pago, confirmado
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    motivo = Column(String, nullable=False)
    modalidad = Column(String, nullable=False, index=True)  # presencial, virtual
    fecha = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    hora = Column(String, nullable=False, index=True)   # HH:MM
    duracion = Column(String, nullable=False)
    costo = Column(Float, nullable=False)
    ubicacion = Column(String, nullable=False)
    token_cancelacion = Column(String, nullable=False, unique=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Índice compuesto para búsquedas rápidas de turnos ocupados
    __table_args__ = (
        Index('idx_modalidad_fecha_hora', 'modalidad', 'fecha', 'hora'),
        Index('idx_estado_fecha_creacion', 'estado', 'fecha_creacion'),
    )
    
    def to_dict(self):
        """
        Convierte el objeto Turno a un diccionario
        (compatible con el formato JSON anterior)
        """
        return {
            "id": self.id,
            "estado": self.estado,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "telefono": self.telefono,
            "motivo": self.motivo,
            "modalidad": self.modalidad,
            "fecha": self.fecha,
            "hora": self.hora,
            "duracion": self.duracion,
            "costo": self.costo,
            "ubicacion": self.ubicacion,
            "token_cancelacion": self.token_cancelacion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f"<Turno(id={self.id}, estado={self.estado}, fecha={self.fecha}, hora={self.hora})>"
