# AOR - Assistant de Réponse aux Appels d'Offre

## Description

AOR est un système intelligent qui automatise la réponse aux appels d'offre en utilisant l'intelligence artificielle. Le système analyse un fichier Excel contenant un appel d'offre, utilise une base de connaissances vectorielle pour trouver les informations pertinentes, et génère automatiquement les réponses appropriées.

## Fonctionnalités

- **Gestion de base de connaissances** : Traitement automatique de fichiers Excel et Word pour créer une base vectorielle
- **Analyse d'appels d'offre** : Extraction et traitement des questions depuis des fichiers Excel
- **Génération de réponses** : Utilisation d'un LLM (Mistral-7B) pour générer des réponses structurées
- **Stockage vectoriel** : Utilisation de Milvus pour le stockage et la recherche de vecteurs
- **Interface modulaire** : Architecture modulaire permettant le test et la maintenance facile

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Fichier Excel │───▶│  Extraction des  │───▶│  Génération de  │
│  Appel d'Offre  │    │    Questions     │    │    Réponses     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Base Vectorielle│    │  Fichier Excel  │
                       │     (Milvus)     │    │   avec Réponses │
                       └──────────────────┘    └─────────────────┘
```

## Installation

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd AOR
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer l'environnement**
   - Créer un fichier `.env` avec les configurations nécessaires
   - Assurer que LMStudio est en cours d'exécution sur `localhost:1234`

4. **Préparer la base de connaissances**
   - Placer vos fichiers de connaissances dans `C:\WokSpace\ABase`
   - Lancer l'application et choisir l'option B pour indexer la base

## Utilisation

### 1. Première utilisation - Indexation de la base de connaissances

```bash
python src/main.py
```

Choisir l'option **B** pour indexer la base de connaissances. Le système va :
- Parcourir tous les fichiers dans `C:\WokSpace\ABase`
- Diviser chaque fichier en chunks
- Générer les embeddings pour chaque chunk
- Stocker les vecteurs dans Milvus

### 2. Répondre à un appel d'offre

1. Choisir l'option **A** dans le menu principal
2. Sélectionner le fichier Excel de l'appel d'offre
3. Le système va :
   - Extraire les questions du fichier
   - Rechercher les chunks pertinents dans la base vectorielle
   - Générer des réponses via le LLM
   - Sauvegarder le fichier avec les réponses dans `C:\WokSpace\AOut`

## Configuration

### Variables d'environnement

Créer un fichier `.env` :

```env
KNOWLEDGE_BASE_PATH=C:\WokSpace\ABase
OUTPUT_PATH=C:\WokSpace\AOut
LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
MILVUS_HOST=localhost
MILVUS_PORT=19530
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.8
```

### Configuration Milvus

Assurez-vous que Milvus est installé et en cours d'exécution :

```bash
# Installation via Docker
docker run -d --name milvus_standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
```

## Structure des modules

### `models/`
- **data_models.py** : Définition des classes Pydantic pour la structure des données

### `services/`
- **embedding_service.py** : Service de génération d'embeddings
- **llm_service.py** : Service d'interaction avec le LLM
- **vector_store_service.py** : Service de gestion de la base vectorielle Milvus
- **excel_service.py** : Service de traitement des fichiers Excel
- **file_processor_service.py** : Service de traitement des fichiers de connaissances

### `utils/`
- **file_utils.py** : Utilitaires pour la manipulation de fichiers
- **json_utils.py** : Utilitaires pour la sérialisation JSON

## Tests

Exécuter les tests unitaires :

```bash
python -m pytest src/tests/
```

## Workflow détaillé

### Phase 1 : Indexation de la base de connaissances
1. **Lecture des fichiers** : Parcours récursif du dossier de connaissances
2. **Extraction du contenu** : Lecture des fichiers Excel et Word
3. **Chunking** : Division du contenu en chunks de taille optimale
4. **Embedding** : Génération de vecteurs pour chaque chunk
5. **Stockage** : Insertion des vecteurs dans Milvus avec métadonnées

### Phase 2 : Traitement d'un appel d'offre
1. **Extraction des questions** : Lecture du fichier Excel d'entrée
2. **Vectorisation** : Génération d'embeddings pour chaque question
3. **Recherche de similarité** : Trouver les chunks les plus pertinents
4. **Génération de réponses** : Utilisation du LLM avec contexte
5. **Sauvegarde** : Mise à jour du fichier Excel avec les réponses

## Modèles utilisés

- **Embedding** : `sentence-transformers/all-MiniLM-L6-v2`
- **LLM** : `mistralai/mistral-7b-instruct-v0.3` (via LMStudio)
- **Base vectorielle** : Milvus

## Format des réponses

Les réponses sont générées au format JSON pour éviter les discussions parasites :

```json
{
  "reponse": "Contenu de la réponse",
  "confiance": 0.85,
  "sources": ["chunk_1", "chunk_2"]
}
```

## Maintenance

### Mise à jour de la base de connaissances
- Relancer l'indexation (option B) pour mettre à jour la base vectorielle
- Les anciens vecteurs sont conservés, les nouveaux sont ajoutés

### Monitoring
- Logs détaillés dans les fichiers de sortie
- Métriques de performance disponibles
- Gestion des erreurs robuste

## Support

Pour toute question ou problème :
1. Vérifier les logs d'erreur
2. S'assurer que tous les services sont en cours d'exécution
3. Contrôler la configuration dans le fichier `.env` 