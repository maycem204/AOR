#!/usr/bin/env python3
"""
Script de lancement pour l'application AOR
"""

import sys
import os

# Ajouter le répertoire src au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Point d'entrée principal"""
    try:
        # Importer et lancer l'application
        from src.main import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Assurez-vous que toutes les dépendances sont installées:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 