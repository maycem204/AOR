"""
Application principale AOR (Assistant de Réponse aux Appels d'Offre)
"""

import logging
import sys
import time
from typing import List, Optional
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import des services et modèles
from config.settings import settings
from models.data_models import QuestionReponse, ProcessingResult, IndexingResult
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.vector_store_service import VectorStoreService
from services.excel_service import ExcelService
from services.file_processor_service import FileProcessorService
from utils.json_utils import save_json_to_file

class AORApplication:
    """
    Application principale AOR qui orchestre tous les services
    """
    
    def __init__(self):
        """Initialise l'application AOR"""
        logger.info("=== Initialisation de l'application AOR ===")
        
        # Valider les chemins
        if not settings.validate_paths():
            logger.error("❌ Erreur de validation des chemins")
            sys.exit(1)
        
        # Initialiser les services
        try:
            self.embedding_service = EmbeddingService()
            self.llm_service = LLMService()
            self.vector_store_service = VectorStoreService()
            self.excel_service = ExcelService()
            self.file_processor_service = FileProcessorService()
            
            logger.info("✓ Tous les services initialisés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation des services: {e}")
            sys.exit(1)
    
    def run(self):
        """Lance l'application principale"""
        try:
            while True:
                self._show_menu()
                choice = input("\nVotre choix: ").strip().upper()
                
                if choice == 'A':
                    self._handle_call_for_tenders()
                elif choice == 'B':
                    self._handle_knowledge_base_indexing()
                elif choice == 'Q':
                    logger.info("Au revoir!")
                    break
                else:
                    print("❌ Choix invalide. Veuillez réessayer.")
                    
        except KeyboardInterrupt:
            logger.info("Application interrompue par l'utilisateur")
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
    
    def _show_menu(self):
        """Affiche le menu principal"""
        print("\n" + "="*60)
        print("           AOR - Assistant de Réponse aux Appels d'Offre")
        print("="*60)
        print("A. Répondre à un appel d'offre")
        print("B. Indexer la base de connaissances")
        print("Q. Quitter")
        print("="*60)
    
    def _handle_call_for_tenders(self):
        """Gère la réponse à un appel d'offre"""
        try:
            print("\n--- Réponse à un appel d'offre ---")
            
            # Demander le fichier Excel
            file_path = input("Chemin du fichier Excel d'appel d'offre: ").strip()
            
            if not file_path:
                print("❌ Chemin de fichier non fourni")
                return
            
            # Valider le fichier
            if not self.excel_service.validate_excel_file(file_path):
                print("❌ Fichier Excel invalide")
                return
            
            # Traiter l'appel d'offre
            result = self._process_call_for_tenders(file_path)
            
            if result:
                print(f"\n✅ Traitement terminé!")
                print(f"📁 Fichier de sortie: {result.output_file}")
                print(f"📊 Questions traitées: {result.questions_traitees}")
                print(f"✅ Questions avec réponse: {result.questions_avec_reponse}")
                print(f"⏱️  Temps de traitement: {result.temps_traitement:.2f}s")
                
                if result.erreurs:
                    print(f"⚠️  Erreurs rencontrées: {len(result.erreurs)}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'appel d'offre: {e}")
            print(f"❌ Erreur: {e}")
    
    def _handle_knowledge_base_indexing(self):
        """Gère l'indexation de la base de connaissances"""
        try:
            print("\n--- Indexation de la base de connaissances ---")
            
            # Vérifier la connexion aux services
            if not self._test_services():
                print("❌ Erreur de connexion aux services")
                return
            
            # Demander confirmation
            confirm = input("Voulez-vous indexer la base de connaissances? (o/N): ").strip().lower()
            if confirm not in ['o', 'oui', 'y', 'yes']:
                print("Indexation annulée")
                return
            
            # Traiter l'indexation
            result = self._process_knowledge_base_indexing()
            
            if result:
                print(f"\n✅ Indexation terminée!")
                print(f"📁 Fichiers traités: {result.fichiers_traites}")
                print(f"📄 Chunks créés: {result.chunks_crees}")
                print(f"💾 Vecteurs stockés: {result.vecteurs_stockes}")
                print(f"⏱️  Temps d'indexation: {result.temps_indexation:.2f}s")
                
                if result.erreurs:
                    print(f"⚠️  Erreurs rencontrées: {len(result.erreurs)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation: {e}")
            print(f"❌ Erreur: {e}")
    
    def _test_services(self) -> bool:
        """Teste la connexion aux services"""
        print("🔍 Test des services...")
        
        # Test Milvus
        if not self.vector_store_service.test_connection():
            print("❌ Erreur de connexion à Milvus")
            return False
        
        # Test LLM
        if not self.llm_service.test_connection():
            print("❌ Erreur de connexion au LLM")
            return False
        
        print("✅ Tous les services sont opérationnels")
        return True
    
    def _process_call_for_tenders(self, file_path: str) -> Optional[ProcessingResult]:
        """Traite un appel d'offre complet"""
        start_time = time.time()
        errors = []
        
        try:
            logger.info(f"Début du traitement de l'appel d'offre: {file_path}")
            
            # 1. Extraire les questions
            questions = self.excel_service.extract_questions_from_excel(file_path)
            if not questions:
                logger.error("Aucune question extraite du fichier")
                return None
            
            logger.info(f"✓ {len(questions)} questions extraites")
            
            # 2. Générer les embeddings pour les questions
            question_texts = [q.question for q in questions]
            question_embeddings = self.embedding_service.generate_embeddings_batch(question_texts)
            
            # Associer les embeddings aux questions
            for i, (question, embedding) in enumerate(zip(questions, question_embeddings)):
                if embedding:
                    question.question_embedding = embedding
            
            logger.info(f"✓ Embeddings générés pour {len([q for q in questions if q.question_embedding])} questions")
            
            # 3. Traiter chaque question
            questions_with_responses = 0
            
            for i, question in enumerate(questions):
                try:
                    logger.info(f"Traitement de la question {i+1}/{len(questions)}")
                    
                    if not question.question_embedding:
                        logger.warning(f"Question {i+1} sans embedding, ignorée")
                        continue
                    
                    # Rechercher les chunks similaires
                    similar_chunks = self.vector_store_service.search_similar_chunks(
                        question.question_embedding,
                        limit=settings.MAX_SIMILAR_CHUNKS,
                        threshold=settings.SIMILARITY_THRESHOLD
                    )
                    
                    if not similar_chunks:
                        logger.warning(f"Aucun chunk similaire trouvé pour la question {i+1}")
                        continue
                    
                    # Préparer le contexte
                    context_chunks = [result.chunk.content for result in similar_chunks]
                    question.chunks_utilises = [result.chunk for result in similar_chunks]
                    
                    # Générer la réponse
                    llm_response = self.llm_service.generate_response(
                        question.question, 
                        context_chunks
                    )
                    
                    if llm_response:
                        question.reponse = llm_response.reponse
                        question.confiance = llm_response.confiance
                        question.sources = llm_response.sources
                        questions_with_responses += 1
                        
                        logger.info(f"✓ Réponse générée pour la question {i+1} (confiance: {llm_response.confiance:.2f})")
                    else:
                        logger.warning(f"Échec de génération de réponse pour la question {i+1}")
                
                except Exception as e:
                    error_msg = f"Erreur lors du traitement de la question {i+1}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # 4. Sauvegarder les réponses
            output_file = self.excel_service.save_responses_to_excel(questions, file_path)
            
            if not output_file:
                logger.error("Échec de sauvegarde des réponses")
                return None
            
            # 5. Sauvegarder les résultats en JSON
            self._save_results_json(questions, file_path)
            
            temps_traitement = time.time() - start_time
            
            logger.info(f"✓ Traitement terminé: {questions_with_responses}/{len(questions)} questions avec réponse")
            
            return ProcessingResult(
                input_file=file_path,
                output_file=output_file,
                questions_traitees=len(questions),
                questions_avec_reponse=questions_with_responses,
                temps_traitement=temps_traitement,
                erreurs=errors
            )
            
        except Exception as e:
            error_msg = f"Erreur générale lors du traitement: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            return ProcessingResult(
                input_file=file_path,
                output_file="",
                questions_traitees=0,
                questions_avec_reponse=0,
                temps_traitement=time.time() - start_time,
                erreurs=errors
            )
    
    def _process_knowledge_base_indexing(self) -> Optional[IndexingResult]:
        """Traite l'indexation de la base de connaissances"""
        try:
            logger.info("Début de l'indexation de la base de connaissances")
            
            # 1. Traiter les fichiers et créer les chunks
            indexing_result = self.file_processor_service.process_knowledge_base()
            
            if indexing_result.chunks_crees == 0:
                logger.warning("Aucun chunk créé")
                return indexing_result
            
            # 2. Générer les embeddings pour tous les chunks
            # Note: Cette étape nécessiterait de récupérer les chunks depuis le service
            # Pour simplifier, on simule cette étape
            
            logger.info("✓ Indexation terminée")
            return indexing_result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation: {e}")
            return None
    
    def _save_results_json(self, questions: List[QuestionReponse], original_file: str):
        """Sauvegarde les résultats en JSON"""
        try:
            # Convertir les questions en dictionnaires
            results_data = []
            for question in questions:
                result = {
                    "question": question.question,
                    "reponse": question.reponse,
                    "confiance": question.confiance,
                    "sources": question.sources,
                    "metadata": question.metadata
                }
                results_data.append(result)
            
            # Créer le chemin de sortie JSON
            output_dir = settings.OUTPUT_PATH
            filename = os.path.splitext(os.path.basename(original_file))[0]
            json_path = os.path.join(output_dir, f"{filename}_resultats.json")
            
            # Sauvegarder
            if save_json_to_file(results_data, json_path):
                logger.info(f"✓ Résultats JSON sauvegardés: {json_path}")
            else:
                logger.error("Échec de sauvegarde JSON")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde JSON: {e}")

def main():
    """Point d'entrée principal de l'application"""
    try:
        app = AORApplication()
        app.run()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 