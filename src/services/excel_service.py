"""
Service de traitement des fichiers Excel pour les appels d'offre
"""

import logging
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
import os
from pathlib import Path

from config.settings import settings
from models.data_models import QuestionReponse, ProcessingResult
from utils.file_utils import ensure_directory_exists, create_backup_file

logger = logging.getLogger(__name__)

class ExcelService:
    """
    Service pour le traitement des fichiers Excel d'appels d'offre
    """
    
    def __init__(self):
        """Initialise le service Excel"""
        logger.info("Initialisation du service Excel")
    
    def extract_questions_from_excel(self, file_path: str) -> List[QuestionReponse]:
        """
        Extrait les questions d'un fichier Excel d'appel d'offre
        
        Args:
            file_path: Chemin du fichier Excel
            
        Returns:
            Liste des questions extraites
        """
        try:
            logger.info(f"Extraction des questions depuis: {file_path}")
            
            # Lire le fichier Excel
            excel_file = pd.ExcelFile(file_path)
            questions = []
            
            # Parcourir toutes les feuilles
            for sheet_name in excel_file.sheet_names:
                logger.debug(f"Traitement de la feuille: {sheet_name}")
                
                # Lire la feuille
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Chercher les colonnes contenant des questions
                question_columns = self._find_question_columns(df)
                
                for col in question_columns:
                    logger.debug(f"Traitement de la colonne: {col}")
                    
                    # Extraire les questions non vides
                    for index, row in df.iterrows():
                        question_text = str(row[col]).strip()
                        
                        if self._is_valid_question(question_text):
                            # Créer l'objet QuestionReponse
                            question_obj = QuestionReponse(
                                question=question_text,
                                reponse=None,  # Sera rempli plus tard
                                question_embedding=None,  # Sera généré plus tard
                                chunks_utilises=[],
                                confiance=None,
                                sources=[],
                                metadata={
                                    "sheet_name": sheet_name,
                                    "column_name": col,
                                    "row_index": index,
                                    "source_file": file_path
                                }
                            )
                            
                            questions.append(question_obj)
            
            logger.info(f"✓ {len(questions)} questions extraites du fichier Excel")
            return questions
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'extraction des questions: {e}")
            return []
    
    def _find_question_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Trouve les colonnes contenant des questions
        
        Args:
            df: DataFrame à analyser
            
        Returns:
            Liste des noms de colonnes contenant des questions
        """
        question_columns = []
        
        for col in df.columns:
            col_str = str(col).lower()
            
            # Mots-clés indiquant des questions
            question_keywords = [
                'question', 'qst', 'interrogation', 'demande', 'requête',
                'sujet', 'thème', 'point', 'item', 'rubrique'
            ]
            
            # Vérifier si le nom de colonne contient des mots-clés
            if any(keyword in col_str for keyword in question_keywords):
                question_columns.append(col)
                continue
            
            # Vérifier le contenu de la colonne
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                # Compter les valeurs qui ressemblent à des questions
                question_count = 0
                for value in non_null_values[:10]:  # Vérifier les 10 premières valeurs
                    if self._is_valid_question(str(value)):
                        question_count += 1
                
                # Si plus de 50% des valeurs sont des questions
                if question_count / min(len(non_null_values), 10) > 0.5:
                    question_columns.append(col)
        
        return question_columns
    
    def _is_valid_question(self, text: str) -> bool:
        """
        Vérifie si un texte est une question valide
        
        Args:
            text: Texte à vérifier
            
        Returns:
            True si c'est une question valide, False sinon
        """
        if not text or text.strip() == '':
            return False
        
        # Ignorer les valeurs NaN, None, etc.
        if text.lower() in ['nan', 'none', 'null', '']:
            return False
        
        # Vérifier la longueur minimale
        if len(text.strip()) < 10:
            return False
        
        # Vérifier qu'il contient des caractères alphabétiques
        if not any(c.isalpha() for c in text):
            return False
        
        return True
    
    def save_responses_to_excel(self, questions: List[QuestionReponse], 
                              original_file_path: str) -> Optional[str]:
        """
        Sauvegarde les réponses dans un nouveau fichier Excel
        
        Args:
            questions: Liste des questions avec leurs réponses
            original_file_path: Chemin du fichier original
            
        Returns:
            Chemin du fichier de sortie ou None en cas d'erreur
        """
        try:
            logger.info(f"Sauvegarde des réponses dans un nouveau fichier Excel")
            
            # Créer le chemin de sortie
            output_path = settings.get_output_file_path(original_file_path)
            
            # S'assurer que le dossier de sortie existe
            ensure_directory_exists(os.path.dirname(output_path))
            
            # Créer une sauvegarde du fichier original
            backup_path = create_backup_file(original_file_path)
            
            # Lire le fichier original
            excel_file = pd.ExcelFile(original_file_path)
            
            # Créer un writer Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                
                # Traiter chaque feuille
                for sheet_name in excel_file.sheet_names:
                    logger.debug(f"Traitement de la feuille: {sheet_name}")
                    
                    # Lire la feuille originale
                    df = pd.read_excel(original_file_path, sheet_name=sheet_name)
                    
                    # Ajouter les réponses
                    df_with_responses = self._add_responses_to_dataframe(df, questions, sheet_name)
                    
                    # Sauvegarder la feuille modifiée
                    df_with_responses.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"✓ Fichier avec réponses sauvegardé: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la sauvegarde des réponses: {e}")
            return None
    
    def _add_responses_to_dataframe(self, df: pd.DataFrame, 
                                  questions: List[QuestionReponse], 
                                  sheet_name: str) -> pd.DataFrame:
        """
        Ajoute les réponses à un DataFrame
        
        Args:
            df: DataFrame original
            questions: Liste des questions avec réponses
            sheet_name: Nom de la feuille
            
        Returns:
            DataFrame avec les réponses ajoutées
        """
        # Créer une copie du DataFrame
        df_with_responses = df.copy()
        
        # Trouver les questions de cette feuille
        sheet_questions = [q for q in questions if q.metadata.get("sheet_name") == sheet_name]
        
        for question in sheet_questions:
            row_index = question.metadata.get("row_index")
            column_name = question.metadata.get("column_name")
            
            if row_index is not None and column_name in df_with_responses.columns:
                # Ajouter la réponse dans une nouvelle colonne
                response_column = f"{column_name}_reponse"
                
                if response_column not in df_with_responses.columns:
                    df_with_responses[response_column] = ""
                
                if question.reponse:
                    df_with_responses.at[row_index, response_column] = question.reponse
                    
                    # Ajouter des métadonnées si disponibles
                    if question.confiance is not None:
                        confidence_column = f"{column_name}_Confiance"
                        if confidence_column not in df_with_responses.columns:
                            df_with_responses[confidence_column] = ""
                        df_with_responses.at[row_index, confidence_column] = question.confiance
                    
                    if question.sources:
                        sources_column = f"{column_name}_Sources"
                        if sources_column not in df_with_responses.columns:
                            df_with_responses[sources_column] = ""
                        df_with_responses.at[row_index, sources_column] = ", ".join(question.sources)
        
        return df_with_responses
    
    def extract_text_from_excel(self, file_path: str) -> str:
        """
        Extrait tout le texte d'un fichier Excel pour l'indexation
        
        Args:
            file_path: Chemin du fichier Excel
            
        Returns:
            Texte extrait du fichier
        """
        try:
            logger.info(f"Extraction du texte depuis: {file_path}")
            
            excel_file = pd.ExcelFile(file_path)
            all_text = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Ajouter le nom de la feuille
                all_text.append(f"=== Feuille: {sheet_name} ===")
                
                # Ajouter les en-têtes
                headers = " | ".join([str(col) for col in df.columns])
                all_text.append(f"En-têtes: {headers}")
                
                # Ajouter le contenu
                for index, row in df.iterrows():
                    row_text = " | ".join([str(val) for val in row.values if pd.notna(val)])
                    if row_text.strip():
                        all_text.append(row_text)
                
                all_text.append("")  # Ligne vide entre les feuilles
            
            full_text = "\n".join(all_text)
            logger.info(f"✓ Texte extrait: {len(full_text)} caractères")
            
            return full_text
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'extraction du texte: {e}")
            return ""
    
    def validate_excel_file(self, file_path: str) -> bool:
        """
        Valide qu'un fichier Excel peut être traité
        
        Args:
            file_path: Chemin du fichier à valider
            
        Returns:
            True si le fichier est valide, False sinon
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Fichier non trouvé: {file_path}")
                return False
            
            # Vérifier l'extension
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                logger.error(f"Extension de fichier non supportée: {file_path}")
                return False
            
            # Tester la lecture du fichier
            excel_file = pd.ExcelFile(file_path)
            
            if len(excel_file.sheet_names) == 0:
                logger.error(f"Aucune feuille trouvée dans: {file_path}")
                return False
            
            logger.info(f"✓ Fichier Excel valide: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la validation du fichier Excel: {e}")
            return False 