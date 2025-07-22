#!/usr/bin/env python3
"""
Script de test pour valider l'installation AOR
"""

import sys
import os
import importlib

def test_imports():
    """Teste l'import des modules principaux"""
    print("🔍 Test des imports...")
    
    modules_to_test = [
        'pandas',
        'openpyxl', 
        'sentence_transformers',
        'pymilvus',
        'requests',
        'python_docx',
        'dotenv',
        'pydantic',
        'numpy',
        'sklearn'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Modules manquants: {', '.join(failed_imports)}")
        print("Installez-les avec: pip install -r requirements.txt")
        return False
    
    print("✅ Tous les imports réussis")
    return True

def test_project_structure():
    """Teste la structure du projet"""
    print("\n🔍 Test de la structure du projet...")
    
    required_files = [
        'src/main.py',
        'src/models/data_models.py',
        'src/services/embedding_service.py',
        'src/services/llm_service.py',
        'src/services/vector_store_service.py',
        'src/services/excel_service.py',
        'src/services/file_processor_service.py',
        'src/utils/file_utils.py',
        'src/utils/json_utils.py',
        'config/settings.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Fichiers manquants: {', '.join(missing_files)}")
        return False
    
    print("✅ Structure du projet correcte")
    return True

def test_configuration():
    """Teste la configuration"""
    print("\n🔍 Test de la configuration...")
    
    try:
        # Ajouter src au path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from config.settings import settings
        
        # Tester les chemins
        if settings.validate_paths():
            print("✅ Chemins de configuration valides")
        else:
            print("⚠️  Certains chemins de configuration sont invalides")
        
        # Afficher la configuration
        print(f"📁 Base de connaissances: {settings.KNOWLEDGE_BASE_PATH}")
        print(f"📁 Dossier de sortie: {settings.OUTPUT_PATH}")
        print(f"🤖 Modèle LLM: {settings.LLM_MODEL}")
        print(f"🔗 Endpoint LLM: {settings.LLM_ENDPOINT}")
        print(f"📊 Modèle embedding: {settings.EMBEDDING_MODEL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return False

def test_services():
    """Teste les services (sans connexion réelle)"""
    print("\n🔍 Test des services...")
    
    try:
        from src.services.embedding_service import EmbeddingService
        from src.services.excel_service import ExcelService
        
        # Test du service Excel (pas besoin de connexion)
        excel_service = ExcelService()
        print("✅ Service Excel initialisé")
        
        # Test du service d'embedding (avec mock)
        try:
            embedding_service = EmbeddingService()
            print("✅ Service d'embedding initialisé")
        except Exception as e:
            print(f"⚠️  Service d'embedding: {e}")
            print("   (Cela peut être normal si sentence-transformers n'est pas installé)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des services: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("="*60)
    print("           TEST D'INSTALLATION AOR")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Structure du projet", test_project_structure),
        ("Configuration", test_configuration),
        ("Services", test_services)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "="*60)
    print("                    RÉSUMÉ")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Installation AOR validée avec succès!")
        print("Vous pouvez maintenant lancer l'application avec:")
        print("python run.py")
    else:
        print(f"\n⚠️  {total - passed} problème(s) détecté(s)")
        print("Vérifiez les erreurs ci-dessus et corrigez-les avant de continuer")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 