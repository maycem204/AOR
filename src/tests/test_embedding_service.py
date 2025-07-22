"""
Tests unitaires pour le service d'embedding
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch

from services.embedding_service import EmbeddingService

class TestEmbeddingService(unittest.TestCase):
    """Tests pour le service d'embedding"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        # Mock du modèle sentence-transformers
        self.mock_model = Mock()
        self.mock_model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        with patch('services.embedding_service.SentenceTransformer') as mock_transformer:
            mock_transformer.return_value = self.mock_model
            self.embedding_service = EmbeddingService()
    
    def test_generate_embedding_success(self):
        """Test de génération d'embedding réussie"""
        text = "Ceci est un test de génération d'embedding"
        
        embedding = self.embedding_service.generate_embedding(text)
        
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 4)
        self.assertTrue(all(isinstance(x, float) for x in embedding))
    
    def test_generate_embedding_empty_text(self):
        """Test avec texte vide"""
        embedding = self.embedding_service.generate_embedding("")
        
        self.assertIsNone(embedding)
    
    def test_generate_embedding_none_text(self):
        """Test avec texte None"""
        embedding = self.embedding_service.generate_embedding(None)
        
        self.assertIsNone(embedding)
    
    def test_generate_embeddings_batch(self):
        """Test de génération d'embeddings en batch"""
        texts = [
            "Premier texte de test",
            "Deuxième texte de test",
            "Troisième texte de test"
        ]
        
        # Mock pour le batch
        self.mock_model.encode.return_value = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 1.1, 1.2]
        ])
        
        embeddings = self.embedding_service.generate_embeddings_batch(texts)
        
        self.assertEqual(len(embeddings), 3)
        self.assertTrue(all(isinstance(emb, list) for emb in embeddings if emb is not None))
    
    def test_calculate_similarity(self):
        """Test de calcul de similarité"""
        embedding1 = [0.1, 0.2, 0.3, 0.4]
        embedding2 = [0.5, 0.6, 0.7, 0.8]
        
        similarity = self.embedding_service.calculate_similarity(embedding1, embedding2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_calculate_similarity_empty_embeddings(self):
        """Test de similarité avec embeddings vides"""
        similarity = self.embedding_service.calculate_similarity([], [])
        
        self.assertEqual(similarity, 0.0)
    
    def test_find_most_similar(self):
        """Test de recherche d'embeddings similaires"""
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        candidate_embeddings = [
            [0.5, 0.6, 0.7, 0.8],
            [0.1, 0.2, 0.3, 0.4],  # Identique
            [0.9, 1.0, 1.1, 1.2]
        ]
        
        results = self.embedding_service.find_most_similar(
            query_embedding, 
            candidate_embeddings, 
            threshold=0.8
        )
        
        self.assertIsInstance(results, list)
        # Le deuxième embedding devrait être trouvé car identique
        self.assertGreater(len(results), 0)
    
    def test_validate_embedding_valid(self):
        """Test de validation d'embedding valide"""
        embedding = [0.1, 0.2, 0.3, 0.4]
        
        is_valid = self.embedding_service.validate_embedding(embedding)
        
        self.assertTrue(is_valid)
    
    def test_validate_embedding_invalid(self):
        """Test de validation d'embedding invalide"""
        # Embedding vide
        is_valid = self.embedding_service.validate_embedding([])
        self.assertFalse(is_valid)
        
        # Embedding avec valeurs non numériques
        is_valid = self.embedding_service.validate_embedding(["a", "b", "c"])
        self.assertFalse(is_valid)
    
    def test_get_embedding_dimension(self):
        """Test de récupération de la dimension d'embedding"""
        dimension = self.embedding_service.get_embedding_dimension()
        
        self.assertIsInstance(dimension, int)
        self.assertGreater(dimension, 0)

if __name__ == '__main__':
    unittest.main() 