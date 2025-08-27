from pymilvus import connections

try:
    # Connexion basique
    connections.connect(alias="default", host="127.0.0.1", port="19530")
    print("✅ Connexion à Milvus réussie !")
except Exception as e:
    print(f"❌ Échec de connexion à Milvus : {e}")
