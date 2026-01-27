from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        """Crea la conexión a Atlas."""
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        print("✅ Conectado a MongoDB Atlas")

    def close(self):
        """Cierra la conexión."""
        if self.client:
            self.client.close()
            print("🛑 Desconectado de MongoDB Atlas")

    def get_db(self):
        """Retorna la base de datos por defecto del cluster."""
        return self.client.get_default_database()

# Instancia global
db = Database()