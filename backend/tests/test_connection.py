"""
Test de Conexión a MongoDB.
Verifica que la conexión a MongoDB Atlas funciona correctamente.
"""
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class TestMongoDBConnection:
    """Tests de conectividad a MongoDB."""

    def test_mongodb_url_configured(self):
        """Verifica que MONGODB_URL está configurada."""
        mongo_uri = os.getenv("MONGODB_URL")
        assert mongo_uri is not None, "MONGODB_URL no está definida en el entorno"
        assert "mongodb" in mongo_uri.lower(), "MONGODB_URL no parece ser una URI válida"

    def test_database_connect(self, db_instance):
        """Verifica que la clase Database se conecta correctamente."""
        assert db_instance._connected is True, "Database no está conectada"
        assert db_instance.client is not None, "Cliente async es None"
        assert db_instance.sync_client is not None, "Cliente sync es None"

    def test_ping_sync_client(self, db_instance):
        """Verifica que el ping al cliente síncrono funciona."""
        try:
            result = db_instance.sync_client.admin.command('ping')
            assert result.get('ok') == 1.0, "Ping no devolvió ok=1"
        except Exception as e:
            pytest.fail(f"Ping falló: {e}")

    @pytest.mark.asyncio
    async def test_health_check(self, db_instance):
        """Verifica el health check asíncrono."""
        result = await db_instance.health_check()
        
        assert "status" in result, "Health check no devuelve status"
        assert result["status"] == "connected 🟢", f"Estado inesperado: {result['status']}"
        assert result.get("latency_ms") is not None, "No hay información de latencia"

    def test_list_collections(self, db_instance):
        """Verifica que se pueden listar colecciones."""
        db = db_instance.sync_client[db_instance.db_name]
        collections = db.list_collection_names()
        
        assert isinstance(collections, list), "list_collection_names no devolvió una lista"
        print(f"\n📁 Colecciones encontradas: {collections}")

    def test_sessions_collection_exists(self, db_instance):
        """Verifica que la colección sessions_metadata existe o se puede crear."""
        db = db_instance.sync_client[db_instance.db_name]
        
        # Insertar y eliminar documento de prueba
        test_doc = {"_test": True, "purpose": "connection_test"}
        result = db["sessions_metadata"].insert_one(test_doc)
        assert result.inserted_id is not None, "No se pudo insertar documento de prueba"
        
        # Limpiar
        db["sessions_metadata"].delete_one({"_id": result.inserted_id})

    def test_checkpoints_collection_accessible(self, db_instance):
        """Verifica que la colección de checkpoints es accesible."""
        db = db_instance.sync_client[db_instance.db_name]
        
        # Solo verificar que podemos hacer count
        count = db["checkpoints"].count_documents({})
        print(f"\n📊 Checkpoints en DB: {count}")
        assert isinstance(count, int), "count_documents no devolvió un entero"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
