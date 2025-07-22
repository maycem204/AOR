"""
Modèles de données Pydantic pour le système AOR
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import numpy as np

class Chunk(BaseModel):
    """Modèle représentant un chunk de texte avec ses métadonnées"""
    
    id: str = Field(..., description="Identifiant unique du chunk")
    content: str = Field(..., description="Contenu textuel du chunk")
    source_file: str = Field(..., description="Fichier source du chunk")
    chunk_index: int = Field(..., description="Index du chunk dans le fichier")
    embedding: Optional[List[float]] = Field(None, description="Vecteur d'embedding du chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées supplémentaires")
    
    class Config:
        arbitrary_types_allowed = True

class VectorSearchResult(BaseModel):
    """Résultat d'une recherche vectorielle"""
    
    chunk: Chunk = Field(..., description="Chunk trouvé")
    similarity_score: float = Field(..., description="Score de similarité (0-1)")
    rank: int = Field(..., description="Rang du résultat")
    
    class Config:
        arbitrary_types_allowed = True

class QuestionReponse(BaseModel):
    """Modèle représentant une question avec sa réponse générée"""
    
    question: str = Field(..., description="Question de l'appel d'offre")
    reponse: Optional[str] = Field(None, description="Réponse générée")
    question_embedding: Optional[List[float]] = Field(None, description="Vecteur d'embedding de la question")
    chunks_utilises: List[Chunk] = Field(default_factory=list, description="Chunks utilisés pour la réponse")
    confiance: Optional[float] = Field(None, description="Niveau de confiance de la réponse (0-1)")
    sources: List[str] = Field(default_factory=list, description="Sources utilisées")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées supplémentaires")
    
    class Config:
        arbitrary_types_allowed = True

class LLMResponse(BaseModel):
    """Réponse structurée du LLM"""
    
    reponse: str = Field(..., description="Contenu de la réponse")
    confiance: float = Field(..., ge=0.0, le=1.0, description="Niveau de confiance")
    sources: List[str] = Field(default_factory=list, description="Sources utilisées")
    
    class Config:
        arbitrary_types_allowed = True

class ProcessingResult(BaseModel):
    """Résultat du traitement d'un fichier"""
    
    input_file: str = Field(..., description="Fichier d'entrée")
    output_file: str = Field(..., description="Fichier de sortie")
    questions_traitees: int = Field(..., description="Nombre de questions traitées")
    questions_avec_reponse: int = Field(..., description="Nombre de questions avec réponse")
    temps_traitement: float = Field(..., description="Temps de traitement en secondes")
    erreurs: List[str] = Field(default_factory=list, description="Erreurs rencontrées")
    
    class Config:
        arbitrary_types_allowed = True

class IndexingResult(BaseModel):
    """Résultat de l'indexation de la base de connaissances"""
    
    fichiers_traites: int = Field(..., description="Nombre de fichiers traités")
    chunks_crees: int = Field(..., description="Nombre de chunks créés")
    vecteurs_stockes: int = Field(..., description="Nombre de vecteurs stockés")
    temps_indexation: float = Field(..., description="Temps d'indexation en secondes")
    erreurs: List[str] = Field(default_factory=list, description="Erreurs rencontrées")
    
    class Config:
        arbitrary_types_allowed = True 