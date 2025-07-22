"""
Utilitaires pour la manipulation de fichiers
"""

import os
import hashlib
import uuid
from typing import List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_chunk_id(content: str, source_file: str, chunk_index: int) -> str:
    """
    Génère un identifiant unique pour un chunk
    
    Args:
        content: Contenu du chunk
        source_file: Fichier source
        chunk_index: Index du chunk
        
    Returns:
        Identifiant unique du chunk
    """
    # Créer un hash du contenu et des métadonnées
    hash_input = f"{content[:100]}_{source_file}_{chunk_index}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()
    return f"chunk_{hash_value}_{uuid.uuid4().hex[:8]}"

def ensure_directory_exists(directory_path: str) -> bool:
    """
    S'assure qu'un répertoire existe, le crée si nécessaire
    
    Args:
        directory_path: Chemin du répertoire
        
    Returns:
        True si le répertoire existe ou a été créé, False sinon
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du répertoire {directory_path}: {e}")
        return False

def get_file_extension(file_path: str) -> str:
    """
    Récupère l'extension d'un fichier
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        Extension du fichier (avec le point)
    """
    return Path(file_path).suffix.lower()

def is_supported_file(file_path: str, supported_extensions: List[str]) -> bool:
    """
    Vérifie si un fichier est supporté
    
    Args:
        file_path: Chemin du fichier
        supported_extensions: Liste des extensions supportées
        
    Returns:
        True si le fichier est supporté, False sinon
    """
    file_extension = get_file_extension(file_path)
    return file_extension in supported_extensions

def get_file_size_mb(file_path: str) -> float:
    """
    Récupère la taille d'un fichier en MB
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        Taille du fichier en MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception as e:
        logger.error(f"Erreur lors du calcul de la taille du fichier {file_path}: {e}")
        return 0.0

def create_backup_file(file_path: str) -> Optional[str]:
    """
    Crée une sauvegarde d'un fichier
    
    Args:
        file_path: Chemin du fichier à sauvegarder
        
    Returns:
        Chemin du fichier de sauvegarde ou None en cas d'erreur
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Fichier {file_path} n'existe pas")
            return None
            
        backup_path = f"{file_path}.backup"
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Sauvegarde créée : {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Erreur lors de la création de la sauvegarde de {file_path}: {e}")
        return None

def clean_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour qu'il soit compatible avec le système de fichiers
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    # Caractères interdits dans les noms de fichiers Windows
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Supprimer les espaces en début et fin
    filename = filename.strip()
    
    # Remplacer les espaces multiples par un seul espace
    filename = ' '.join(filename.split())
    
    return filename

def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Récupère le chemin relatif d'un fichier par rapport à un répertoire de base
    
    Args:
        file_path: Chemin absolu du fichier
        base_path: Chemin absolu du répertoire de base
        
    Returns:
        Chemin relatif du fichier
    """
    try:
        return os.path.relpath(file_path, base_path)
    except ValueError:
        # Si les chemins sont sur des lecteurs différents
        return file_path

def count_files_in_directory(directory_path: str, extensions: Optional[List[str]] = None) -> int:
    """
    Compte le nombre de fichiers dans un répertoire
    
    Args:
        directory_path: Chemin du répertoire
        extensions: Liste des extensions à compter (si None, compte tous les fichiers)
        
    Returns:
        Nombre de fichiers
    """
    count = 0
    try:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if extensions is None or get_file_extension(file) in extensions:
                    count += 1
    except Exception as e:
        logger.error(f"Erreur lors du comptage des fichiers dans {directory_path}: {e}")
    
    return count 