"""
Configuration du système AOR (Assistant de Réponse aux Appels d'Offre)
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class Settings:
    """Configuration centralisée du système AOR"""
    
    # Chemins des dossiers
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", r"C:\WokSpace\ABase")
    OUTPUT_PATH: str = os.getenv("OUTPUT_PATH", r"C:\WokSpace\AOut")
    
    # Configuration LLM
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "http://localhost:1234/v1/chat/completions")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct-v0.3")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # Configuration Milvus
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_COLLECTION_NAME: str = os.getenv("MILVUS_COLLECTION_NAME", "aor_knowledge_base")
    MILVUS_DIMENSION: int = int(os.getenv("MILVUS_DIMENSION", "384"))  # Dimension pour all-MiniLM-L6-v2
    
    # Configuration Embedding
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    
    # Configuration de similarité
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
    MAX_SIMILAR_CHUNKS: int = int(os.getenv("MAX_SIMILAR_CHUNKS", "5"))
    
    # Configuration de chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Configuration des fichiers
    SUPPORTED_EXCEL_EXTENSIONS: list = [".xlsx", ".xls"]
    SUPPORTED_WORD_EXTENSIONS: list = [".docx", ".doc"]
    SUPPORTED_EXTENSIONS: list = SUPPORTED_EXCEL_EXTENSIONS + SUPPORTED_WORD_EXTENSIONS
    
    # Configuration des logs
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "aor.log")
    
    # Configuration des prompts
    SYSTEM_PROMPT: str = """Tu es un assistant spécialisé dans la réponse aux appels d'offre.
Tu dois répondre de manière précise et professionnelle en te basant sur les informations fournies.
Réponds UNIQUEMENT au format JSON suivant :
{
    "reponse": "Contenu de la réponse",
    "confiance": 0.85,
    "sources": ["source1", "source2"]
}"""

    @classmethod
    def validate_paths(cls) -> bool:
        """Valide que les chemins de base existent"""
        paths_to_check = [
            cls.KNOWLEDGE_BASE_PATH,
            cls.OUTPUT_PATH
        ]
        
        for path in paths_to_check:
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"✓ Dossier créé : {path}")
                except Exception as e:
                    print(f"✗ Erreur lors de la création du dossier {path}: {e}")
                    return False
        
        return True
    
    @classmethod
    def get_knowledge_base_files(cls) -> list:
        """Récupère la liste des fichiers de la base de connaissances"""
        files = []
        if os.path.exists(cls.KNOWLEDGE_BASE_PATH):
            for root, dirs, filenames in os.walk(cls.KNOWLEDGE_BASE_PATH):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if any(filename.lower().endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):
                        files.append(file_path)
        return files
    
    @classmethod
    def get_output_file_path(cls, input_file_path: str) -> str:
        """Génère le chemin de sortie pour un fichier d'entrée"""
        input_filename = os.path.basename(input_file_path)
        name, ext = os.path.splitext(input_filename)
        output_filename = f"{name}_avec_reponses{ext}"
        return os.path.join(cls.OUTPUT_PATH, output_filename)

# Instance globale des paramètres
settings = Settings() 