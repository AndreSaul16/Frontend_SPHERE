"""
Script de análisis de datos en MongoDB
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('DB_NAME', 'sphere_db')]
coll = db['knowledge_base']

total = coll.count_documents({})
print(f"📊 Total de documentos: {total}\n")

# Agrupar por fuente
print("📁 Por fuente:")
pipeline = [{'$group': {'_id': '$source', 'count': {'$sum': 1}}}]
result = list(coll.aggregate(pipeline))

for doc in sorted(result, key=lambda x: x['count'], reverse=True):
    print(f"   {doc['_id']}: {doc['count']} docs")

# Agrupar por agent_target
print("\n👤 Por agente:")
pipeline = [{'$group': {'_id': '$agent_target', 'count': {'$sum': 1}}}]
result = list(coll.aggregate(pipeline))

for doc in sorted(result, key=lambda x: x['count'], reverse=True):
    agent = doc['_id'] if doc['_id'] else 'Sin asignar'
    print(f"   {agent}: {doc['count']} docs")
