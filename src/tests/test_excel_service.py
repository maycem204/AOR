"""
Tests unitaires pour le service Excel
"""

import unittest
import tempfile
import os
import pandas as pd
from unittest.mock import Mock, patch

from services.excel_service import ExcelService

class TestExcelService(unittest.TestCase):
    """Tests pour le service Excel"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.excel_service = ExcelService()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_excel_file(self, data, filename="test.xlsx"):
        """Crée un fichier Excel de test"""
        file_path = os.path.join(self.temp_dir, filename)
        
        # Créer un DataFrame
        df = pd.DataFrame(data)
        
        # Sauvegarder en Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)
        
        return file_path
    
    def test_validate_excel_file_valid(self):
        """Test de validation d'un fichier Excel valide"""
        # Créer un fichier Excel de test
        test_data = {
            'Question': ['Question 1', 'Question 2', 'Question 3'],
            'Description': ['Desc 1', 'Desc 2', 'Desc 3']
        }
        file_path = self.create_test_excel_file(test_data)
        
        is_valid = self.excel_service.validate_excel_file(file_path)
        
        self.assertTrue(is_valid)
    
    def test_validate_excel_file_nonexistent(self):
        """Test de validation d'un fichier inexistant"""
        is_valid = self.excel_service.validate_excel_file("fichier_inexistant.xlsx")
        
        self.assertFalse(is_valid)
    
    def test_validate_excel_file_wrong_extension(self):
        """Test de validation d'un fichier avec mauvaise extension"""
        # Créer un fichier texte
        file_path = os.path.join(self.temp_dir, "test.txt")
        with open(file_path, 'w') as f:
            f.write("test")
        
        is_valid = self.excel_service.validate_excel_file(file_path)
        
        self.assertFalse(is_valid)
    
    def test_extract_questions_from_excel(self):
        """Test d'extraction de questions depuis Excel"""
        test_data = {
            'Question': [
                'Quelle est la politique de sécurité?',
                'Comment gérer les accès utilisateurs?',
                'Quels sont les SLA?'
            ],
            'Réponse': ['', '', ''],
            'Notes': ['Note 1', 'Note 2', 'Note 3']
        }
        file_path = self.create_test_excel_file(test_data)
        
        questions = self.excel_service.extract_questions_from_excel(file_path)
        
        self.assertIsInstance(questions, list)
        self.assertEqual(len(questions), 3)
        
        # Vérifier que les questions sont extraites correctement
        for question in questions:
            self.assertIsNotNone(question.question)
            self.assertIn('Question', question.metadata['column_name'])
    
    def test_extract_questions_from_excel_no_questions(self):
        """Test d'extraction avec aucune question"""
        test_data = {
            'Nom': ['John', 'Jane', 'Bob'],
            'Age': [25, 30, 35],
            'Ville': ['Paris', 'Lyon', 'Marseille']
        }
        file_path = self.create_test_excel_file(test_data)
        
        questions = self.excel_service.extract_questions_from_excel(file_path)
        
        self.assertEqual(len(questions), 0)
    
    def test_is_valid_question(self):
        """Test de validation de questions"""
        # Questions valides
        self.assertTrue(self.excel_service._is_valid_question("Quelle est la politique de sécurité?"))
        self.assertTrue(self.excel_service._is_valid_question("Comment gérer les accès utilisateurs?"))
        
        # Questions invalides
        self.assertFalse(self.excel_service._is_valid_question(""))
        self.assertFalse(self.excel_service._is_valid_question("   "))
        self.assertFalse(self.excel_service._is_valid_question("nan"))
        self.assertFalse(self.excel_service._is_valid_question("123"))
        self.assertFalse(self.excel_service._is_valid_question("a"))  # Trop court
    
    def test_find_question_columns(self):
        """Test de recherche de colonnes de questions"""
        test_data = {
            'Question': ['Q1', 'Q2'],
            'Question Technique': ['QT1', 'QT2'],
            'Nom': ['John', 'Jane'],
            'Question Sécurité': ['QS1', 'QS2']
        }
        df = pd.DataFrame(test_data)
        
        question_columns = self.excel_service._find_question_columns(df)
        
        # Devrait trouver les colonnes contenant "Question"
        expected_columns = ['Question', 'Question Technique', 'Question Sécurité']
        self.assertEqual(set(question_columns), set(expected_columns))
    
    def test_extract_text_from_excel(self):
        """Test d'extraction de texte depuis Excel"""
        test_data = {
            'Question': ['Q1', 'Q2'],
            'Réponse': ['R1', 'R2'],
            'Notes': ['Note 1', 'Note 2']
        }
        file_path = self.create_test_excel_file(test_data)
        
        text = self.excel_service.extract_text_from_excel(file_path)
        
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        self.assertIn('Sheet1', text)
        self.assertIn('Question', text)
        self.assertIn('Réponse', text)
    
    def test_save_responses_to_excel(self):
        """Test de sauvegarde de réponses en Excel"""
        from models.data_models import QuestionReponse
        
        # Créer des questions avec réponses
        questions = [
            QuestionReponse(
                question="Quelle est la politique de sécurité?",
                reponse="La politique de sécurité inclut...",
                confiance=0.85,
                sources=["doc1", "doc2"],
                metadata={
                    "sheet_name": "Sheet1",
                    "column_name": "Question",
                    "row_index": 0
                }
            ),
            QuestionReponse(
                question="Comment gérer les accès?",
                reponse="Les accès sont gérés via...",
                confiance=0.92,
                sources=["doc3"],
                metadata={
                    "sheet_name": "Sheet1",
                    "column_name": "Question",
                    "row_index": 1
                }
            )
        ]
        
        # Créer un fichier Excel original
        test_data = {
            'Question': [
                'Quelle est la politique de sécurité?',
                'Comment gérer les accès?'
            ]
        }
        original_file = self.create_test_excel_file(test_data, "original.xlsx")
        
        # Sauvegarder les réponses
        output_file = self.excel_service.save_responses_to_excel(questions, original_file)
        
        self.assertIsNotNone(output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # Vérifier que le fichier contient les réponses
        df = pd.read_excel(output_file, sheet_name='Sheet1')
        self.assertIn('Question_Réponse', df.columns)
        self.assertIn('Question_Confiance', df.columns)
        self.assertIn('Question_Sources', df.columns)

if __name__ == '__main__':
    unittest.main() 