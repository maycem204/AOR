"""
Service LLM pour interagir avec le modèle Mistral via LMStudio
"""

import logging
import requests
import json
from typing import List, Optional, Dict, Any
import time

from config.settings import settings
from models.data_models import LLMResponse
from utils.json_utils import extract_json_from_text, validate_json_structure

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service pour interagir avec le LLM via l'API LMStudio
    """
    
    def __init__(self, endpoint: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise le service LLM
        
        Args:
            endpoint: Endpoint de l'API LMStudio
            model: Nom du modèle à utiliser
        """
        self.endpoint = endpoint or settings.LLM_ENDPOINT
        self.model = model or settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        
        logger.info(f"Initialisation du service LLM avec l'endpoint: {self.endpoint}")
        logger.info(f"Modèle utilisé: {self.model}")
        
        # Tester la connexion
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """
        Teste la connexion à l'API LMStudio
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            response = requests.get(self.endpoint.replace("/v1/chat/completions", "/v1/models"), 
                                 timeout=10)
            if response.status_code == 200:
                logger.info("✓ Connexion à LMStudio réussie")
                return True
            else:
                logger.warning(f"⚠️ Connexion à LMStudio: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ Erreur de connexion à LMStudio: {e}")
            return False
    
    def _create_chat_message(self, question: str, context_chunks: List[str]) -> List[Dict[str, str]]:
        """
        Crée le message de chat pour l'API
        
        Args:
            question: Question à poser
            context_chunks: Chunks de contexte à utiliser
            
        Returns:
            Liste de messages pour l'API
        """
        # Construire le contexte
        context_text = "\n\n".join([f"Contexte {i+1}: {chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Créer le prompt utilisateur
        user_prompt = f"""Question: {question}

Contexte disponible:
{context_text}

Réponds UNIQUEMENT au format JSON suivant:
{{
    "reponse": "Contenu de la réponse",
    "confiance": 0.85,
    "sources": ["source1", "source2"]
}}"""
        
        return [
            {"role": "system", "content": settings.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    
    def generate_response(self, question: str, context_chunks: List[str], 
                         max_retries: int = 3) -> Optional[LLMResponse]:
        """
        Génère une réponse à une question en utilisant le contexte fourni
        
        Args:
            question: Question à poser
            context_chunks: Chunks de contexte à utiliser
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Réponse structurée du LLM ou None en cas d'échec
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Tentative {attempt + 1}/{max_retries} pour la question: {question[:50]}...")
                
                # Créer le message de chat
                messages = self._create_chat_message(question, context_chunks)
                
                # Préparer la requête
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": False
                }
                
                # Envoyer la requête
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code != 200:
                    logger.error(f"Erreur API: {response.status_code} - {response.text}")
                    continue
                
                # Parser la réponse
                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not content:
                    logger.warning("Réponse vide du LLM")
                    continue
                
                # Extraire le JSON de la réponse
                json_data = extract_json_from_text(content)
                if not json_data:
                    logger.warning("Aucun JSON trouvé dans la réponse du LLM")
                    continue
                
                # Valider la structure JSON
                required_keys = ["reponse", "confiance"]
                if not validate_json_structure(json_data, required_keys):
                    logger.warning("Structure JSON invalide dans la réponse")
                    continue
                
                # Créer l'objet de réponse
                llm_response = LLMResponse(
                    reponse=json_data.get("reponse", ""),
                    confiance=float(json_data.get("confiance", 0.0)),
                    sources=json_data.get("sources", [])
                )
                
                logger.info(f"✓ Réponse générée avec confiance: {llm_response.confiance}")
                return llm_response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout lors de la tentative {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
                continue
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération de réponse (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue
        
        logger.error(f"Échec de génération de réponse après {max_retries} tentatives")
        return None
    
    def generate_responses_batch(self, questions_with_context: List[tuple], 
                               max_retries: int = 3) -> List[Optional[LLMResponse]]:
        """
        Génère des réponses pour plusieurs questions en batch
        
        Args:
            questions_with_context: Liste de tuples (question, context_chunks)
            max_retries: Nombre maximum de tentatives par question
            
        Returns:
            Liste de réponses (None pour les échecs)
        """
        results = []
        
        for i, (question, context_chunks) in enumerate(questions_with_context):
            logger.info(f"Traitement de la question {i+1}/{len(questions_with_context)}")
            
            response = self.generate_response(question, context_chunks, max_retries)
            results.append(response)
            
            # Pause entre les requêtes pour éviter la surcharge
            if i < len(questions_with_context) - 1:
                time.sleep(0.5)
        
        return results
    
    def test_connection(self) -> bool:
        """
        Teste la connexion au service LLM
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            test_question = "Test de connexion"
            test_context = ["Ceci est un test de connexion au service LLM."]
            
            response = self.generate_response(test_question, test_context, max_retries=1)
            
            if response and response.reponse:
                logger.info("✓ Test de connexion LLM réussi")
                return True
            else:
                logger.warning("⚠️ Test de connexion LLM échoué")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur lors du test de connexion LLM: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Récupère les informations sur le modèle utilisé
        
        Returns:
            Dictionnaire avec les informations du modèle
        """
        try:
            response = requests.get(
                self.endpoint.replace("/v1/chat/completions", "/v1/models"),
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                for model in models:
                    if model.get("id") == self.model:
                        return {
                            "model_id": model.get("id"),
                            "object": model.get("object"),
                            "created": model.get("created"),
                            "owned_by": model.get("owned_by")
                        }
            
            return {"model_id": self.model, "status": "unknown"}
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du modèle: {e}")
            return {"model_id": self.model, "status": "error"} 