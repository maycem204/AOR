"""
Service de génération d'embeddings pour le système AOR
"""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service pour la génération d'embeddings de texte
    Utilise sentence-transformers pour générer des vecteurs de représentation
    """
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialise le service d'embedding
        
        Args:
            model_name: Nom du modèle à utiliser (par défaut depuis settings)
            device: Device à utiliser ('cpu' ou 'cuda')
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE
        
        logger.info(f"Initialisation du service d'embedding avec le modèle: {self.model_name}")
        logger.info(f"Device utilisé: {self.device}")
        
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("✓ Modèle d'embedding chargé avec succès")
        except Exception as e:
            logger.error(f"✗ Erreur lors du chargement du modèle d'embedding: {e}")
            raise
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Génère un embedding pour un texte donné
        
        Args:
            text: Texte à encoder
            
        Returns:
            Liste de floats représentant le vecteur d'embedding
        """
        try:
            if not text or not text.strip():
                logger.warning("Texte vide fourni pour l'embedding")
                return None
            
            # Nettoyer le texte
            cleaned_text = text.strip()
            
            # Générer l'embedding
            embedding = self.model.encode(cleaned_text, convert_to_tensor=False)
            
            # Convertir en liste de floats
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            logger.debug(f"Embedding généré pour un texte de {len(cleaned_text)} caractères")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Génère des embeddings pour une liste de textes (optimisé pour le batch)
        
        Args:
            texts: Liste de textes à encoder
            
        Returns:
            Liste d'embeddings (None pour les textes qui ont échoué)
        """
        try:
            if not texts:
                logger.warning("Liste de textes vide fournie")
                return []
            
            # Filtrer les textes vides
            valid_texts = [(i, text.strip()) for i, text in enumerate(texts) if text and text.strip()]
            
            if not valid_texts:
                logger.warning("Aucun texte valide trouvé dans la liste")
                return [None] * len(texts)
            
            # Extraire les indices et textes valides
            indices, cleaned_texts = zip(*valid_texts)
            
            # Générer les embeddings en batch
            embeddings = self.model.encode(cleaned_texts, convert_to_tensor=False)
            
            # Créer la liste de résultats
            results = [None] * len(texts)
            for i, (original_idx, embedding) in enumerate(zip(indices, embeddings)):
                results[original_idx] = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            logger.info(f"Embeddings générés pour {len(valid_texts)}/{len(texts)} textes")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embeddings en batch: {e}")
            return [None] * len(texts)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier vecteur d'embedding
            embedding2: Deuxième vecteur d'embedding
            
        Returns:
            Score de similarité entre 0 et 1
        """
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            # Convertir en numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculer la similarité cosinus
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # S'assurer que le résultat est entre 0 et 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de similarité: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         threshold: float = 0.8) -> List[tuple]:
        """
        Trouve les embeddings les plus similaires à un embedding de requête
        
        Args:
            query_embedding: Embedding de la requête
            candidate_embeddings: Liste d'embeddings candidats
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste de tuples (index, score) triés par score décroissant
        """
        try:
            similarities = []
            
            for i, candidate_embedding in enumerate(candidate_embeddings):
                if candidate_embedding is not None:
                    similarity = self.calculate_similarity(query_embedding, candidate_embedding)
                    if similarity >= threshold:
                        similarities.append((i, similarity))
            
            # Trier par score décroissant
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            logger.debug(f"Trouvé {len(similarities)} embeddings similaires (seuil: {threshold})")
            return similarities
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'embeddings similaires: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """
        Récupère la dimension des embeddings générés par le modèle
        
        Returns:
            Dimension des vecteurs d'embedding
        """
        try:
            # Générer un embedding de test pour obtenir la dimension
            test_embedding = self.model.encode("test", convert_to_tensor=False)
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la dimension d'embedding: {e}")
            return settings.MILVUS_DIMENSION
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Valide qu'un embedding est correct
        
        Args:
            embedding: Vecteur d'embedding à valider
            
        Returns:
            True si l'embedding est valide, False sinon
        """
        try:
            if not embedding:
                return False
            
            # Vérifier que c'est une liste de nombres
            if not all(isinstance(x, (int, float)) for x in embedding):
                return False
            
            # Vérifier qu'il n'y a pas de valeurs NaN ou infinies
            if any(np.isnan(x) or np.isinf(x) for x in embedding):
                return False
            
            # Vérifier la dimension
            expected_dim = self.get_embedding_dimension()
            if len(embedding) != expected_dim:
                logger.warning(f"Dimension d'embedding incorrecte: {len(embedding)} vs {expected_dim}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation d'embedding: {e}")
            return False 