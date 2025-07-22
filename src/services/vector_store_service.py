"""
Service de gestion de la base vectorielle Milvus
"""

import logging
from typing import List, Optional, Dict, Any
import time

from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from pymilvus.exceptions import MilvusException

from config.settings import settings
from models.data_models import Chunk, VectorSearchResult

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Service pour la gestion de la base vectorielle Milvus
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialise le service de base vectorielle
        
        Args:
            host: Hôte Milvus
            port: Port Milvus
        """
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dimension = settings.MILVUS_DIMENSION
        
        logger.info(f"Initialisation du service Milvus: {self.host}:{self.port}")
        
        # Connexion à Milvus
        self._connect()
        
        # Initialiser la collection
        self._init_collection()
    
    def _connect(self) -> bool:
        """
        Établit la connexion à Milvus
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info("✓ Connexion à Milvus réussie")
            return True
        except Exception as e:
            logger.error(f"✗ Erreur de connexion à Milvus: {e}")
            return False
    
    def _init_collection(self) -> bool:
        """
        Initialise la collection Milvus
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        try:
            # Vérifier si la collection existe
            if utility.has_collection(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' existe déjà")
                return True
            
            # Définir le schéma de la collection
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=65535, is_primary=True),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
            ]
            
            schema = CollectionSchema(fields=fields, description="Base de connaissances AOR")
            
            # Créer la collection
            collection = Collection(name=self.collection_name, schema=schema)
            
            # Créer l'index
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"✓ Collection '{self.collection_name}' créée avec succès")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'initialisation de la collection: {e}")
            return False
    
    def insert_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Insère des chunks dans la base vectorielle
        
        Args:
            chunks: Liste de chunks à insérer
            
        Returns:
            True si l'insertion réussit, False sinon
        """
        try:
            if not chunks:
                logger.warning("Aucun chunk à insérer")
                return True
            
            collection = Collection(self.collection_name)
            
            # Préparer les données
            ids = []
            contents = []
            source_files = []
            chunk_indices = []
            embeddings = []
            metadatas = []
            
            for chunk in chunks:
                if not chunk.embedding:
                    logger.warning(f"Chunk {chunk.id} sans embedding, ignoré")
                    continue
                
                ids.append(chunk.id)
                contents.append(chunk.content)
                source_files.append(chunk.source_file)
                chunk_indices.append(chunk.chunk_index)
                embeddings.append(chunk.embedding)
                metadatas.append(str(chunk.metadata))
            
            if not ids:
                logger.warning("Aucun chunk valide à insérer")
                return True
            
            # Insérer les données
            data = [ids, contents, source_files, chunk_indices, embeddings, metadatas]
            collection.insert(data)
            
            # Flush pour s'assurer que les données sont persistées
            collection.flush()
            
            logger.info(f"✓ {len(ids)} chunks insérés dans Milvus")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'insertion des chunks: {e}")
            return False
    
    def search_similar_chunks(self, query_embedding: List[float], 
                            limit: int = 5, threshold: float = 0.8) -> List[VectorSearchResult]:
        """
        Recherche les chunks les plus similaires à un embedding de requête
        
        Args:
            query_embedding: Embedding de la requête
            limit: Nombre maximum de résultats
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des résultats de recherche
        """
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            # Paramètres de recherche
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Effectuer la recherche
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=["id", "content", "source_file", "chunk_index", "metadata"]
            )
            
            # Traiter les résultats
            search_results = []
            for hits in results:
                for hit in hits:
                    if hit.score >= threshold:
                        # Créer l'objet Chunk
                        chunk = Chunk(
                            id=hit.entity.get("id"),
                            content=hit.entity.get("content"),
                            source_file=hit.entity.get("source_file"),
                            chunk_index=hit.entity.get("chunk_index"),
                            embedding=query_embedding,  # On ne stocke pas l'embedding original
                            metadata=eval(hit.entity.get("metadata", "{}"))
                        )
                        
                        # Créer le résultat de recherche
                        search_result = VectorSearchResult(
                            chunk=chunk,
                            similarity_score=hit.score,
                            rank=len(search_results) + 1
                        )
                        
                        search_results.append(search_result)
            
            logger.info(f"✓ {len(search_results)} chunks similaires trouvés (seuil: {threshold})")
            return search_results
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la recherche de chunks similaires: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de la collection
        
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            collection = Collection(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "num_entities": collection.num_entities,
                "schema": str(collection.schema),
                "indexes": collection.indexes
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """
        Vide la collection (supprime tous les vecteurs)
        
        Returns:
            True si la suppression réussit, False sinon
        """
        try:
            collection = Collection(self.collection_name)
            collection.delete("id like '%'")  # Supprimer tous les vecteurs
            collection.flush()
            
            logger.info(f"✓ Collection '{self.collection_name}' vidée")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors du vidage de la collection: {e}")
            return False
    
    def delete_chunks_by_source(self, source_file: str) -> bool:
        """
        Supprime tous les chunks d'un fichier source
        
        Args:
            source_file: Chemin du fichier source
            
        Returns:
            True si la suppression réussit, False sinon
        """
        try:
            collection = Collection(self.collection_name)
            collection.delete(f'source_file == "{source_file}"')
            collection.flush()
            
            logger.info(f"✓ Chunks supprimés pour le fichier: {source_file}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la suppression des chunks: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à Milvus
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            # Vérifier la connexion
            if not connections.has_connection("default"):
                return self._connect()
            
            # Vérifier que la collection existe
            if not utility.has_collection(self.collection_name):
                return self._init_collection()
            
            logger.info("✓ Test de connexion Milvus réussi")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors du test de connexion Milvus: {e}")
            return False
    
    def __del__(self):
        """
        Destructeur pour fermer la connexion
        """
        try:
            connections.disconnect("default")
        except:
            pass 