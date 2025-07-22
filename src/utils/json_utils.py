"""
Utilitaires pour la manipulation JSON
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def safe_json_loads(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Charge une chaîne JSON de manière sécurisée
    
    Args:
        json_string: Chaîne JSON à parser
        
    Returns:
        Dictionnaire parsé ou None en cas d'erreur
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du parsing JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du parsing JSON: {e}")
        return None

def safe_json_dumps(obj: Any, indent: int = 2) -> Optional[str]:
    """
    Sérialise un objet en JSON de manière sécurisée
    
    Args:
        obj: Objet à sérialiser
        indent: Indentation pour le formatage
        
    Returns:
        Chaîne JSON ou None en cas d'erreur
    """
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=False)
    except TypeError as e:
        logger.error(f"Erreur lors de la sérialisation JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la sérialisation JSON: {e}")
        return None

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extrait un objet JSON d'un texte qui peut contenir du texte avant/après
    
    Args:
        text: Texte contenant potentiellement du JSON
        
    Returns:
        Dictionnaire JSON extrait ou None si non trouvé
    """
    try:
        # Chercher des accolades ouvrantes et fermantes
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_part = text[start_idx:end_idx + 1]
            return safe_json_loads(json_part)
        
        return None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction JSON: {e}")
        return None

def validate_json_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Valide qu'un dictionnaire contient les clés requises
    
    Args:
        data: Dictionnaire à valider
        required_keys: Liste des clés requises
        
    Returns:
        True si toutes les clés sont présentes, False sinon
    """
    if not isinstance(data, dict):
        return False
    
    return all(key in data for key in required_keys)

def pydantic_to_dict(model: BaseModel) -> Dict[str, Any]:
    """
    Convertit un modèle Pydantic en dictionnaire
    
    Args:
        model: Modèle Pydantic
        
    Returns:
        Dictionnaire représentant le modèle
    """
    try:
        return model.dict()
    except Exception as e:
        logger.error(f"Erreur lors de la conversion Pydantic vers dict: {e}")
        return {}

def save_json_to_file(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Sauvegarde des données en JSON dans un fichier
    
    Args:
        data: Données à sauvegarder
        file_path: Chemin du fichier de sortie
        indent: Indentation pour le formatage
        
    Returns:
        True si la sauvegarde a réussi, False sinon
    """
    try:
        json_string = safe_json_dumps(data, indent)
        if json_string is None:
            return False
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_string)
        
        logger.info(f"Données JSON sauvegardées dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde JSON dans {file_path}: {e}")
        return False

def load_json_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Charge des données JSON depuis un fichier
    
    Args:
        file_path: Chemin du fichier à charger
        
    Returns:
        Dictionnaire chargé ou None en cas d'erreur
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"Fichier non trouvé: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Erreur JSON dans le fichier {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier {file_path}: {e}")
        return None

def merge_json_objects(obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne deux objets JSON (obj2 écrase obj1 en cas de conflit)
    
    Args:
        obj1: Premier objet JSON
        obj2: Deuxième objet JSON
        
    Returns:
        Objet JSON fusionné
    """
    result = obj1.copy()
    result.update(obj2)
    return result

def flatten_json(obj: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    Aplatit un objet JSON imbriqué
    
    Args:
        obj: Objet JSON à aplatir
        prefix: Préfixe pour les clés (utilisé en récursion)
        
    Returns:
        Objet JSON aplati
    """
    flattened = {}
    
    for key, value in obj.items():
        new_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            flattened.update(flatten_json(value, new_key))
        else:
            flattened[new_key] = value
    
    return flattened 