#!/bin/bash

# Script de validation complète pour l'intégration PostGIS + pg_vector
# Ce script vérifie que tous les composants sont correctement implémentés

set -e  # Exit on any error

echo "🔍 VALIDATION COMPLÈTE - INTÉGRATION PostGIS + pg_vector"
echo "=================================================="

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les résultats
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Variables de validation
ERRORS=0
WARNINGS=0

echo ""
echo "📋 1. VALIDATION STRUCTURE DE FICHIERS"
echo "======================================="

# Vérifier fichiers principaux
check_file() {
    if [ -f "$1" ]; then
        print_result 0 "Fichier $1 présent"
    else
        print_result 1 "Fichier $1 manquant"
        ERRORS=$((ERRORS + 1))
    fi
}

# Types Python
check_file "sandbox/grist/usertypes.py"

# Types TypeScript
check_file "app/common/gristTypes.ts"
check_file "app/plugin/GristData.ts"

# Widgets
check_file "app/client/widgets/GeometryEditor.ts"
check_file "app/client/widgets/VectorEditor.ts"
check_file "app/client/widgets/UserType.ts"
check_file "app/client/widgets/UserTypeImpl.ts"

# Migration
check_file "app/gen-server/migration/1750000000000-PostgresExtensions.ts"

# Tests
check_file "test/python/test_new_usertypes.py"
check_file "test/client/widgets/GeometryVectorWidgets.ts"
check_file "test/server/postgis-pgvector.ts"
check_file "test/integration/test_postgis_pgvector_integration.ts"

# Documentation
check_file "documentation/postgis-pgvector-support.md"

echo ""
echo "🔍 2. VALIDATION CONTENU DES FICHIERS"
echo "====================================="

# Vérifier que les types sont ajoutés dans _type_defaults
if grep -q "'Geometry':" sandbox/grist/usertypes.py; then
    print_result 0 "Type Geometry ajouté dans _type_defaults"
else
    print_result 1 "Type Geometry manquant dans _type_defaults"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "'Vector':" sandbox/grist/usertypes.py; then
    print_result 0 "Type Vector ajouté dans _type_defaults"
else
    print_result 1 "Type Vector manquant dans _type_defaults"
    ERRORS=$((ERRORS + 1))
fi

# Vérifier classes Python
if grep -q "class Geometry(BaseColumnType):" sandbox/grist/usertypes.py; then
    print_result 0 "Classe Geometry définie"
else
    print_result 1 "Classe Geometry non trouvée"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "class Vector(BaseColumnType):" sandbox/grist/usertypes.py; then
    print_result 0 "Classe Vector définie"  
else
    print_result 1 "Classe Vector non trouvée"
    ERRORS=$((ERRORS + 1))
fi

# Vérifier TypeScript types
if grep -q "'Geometry'" app/common/gristTypes.ts; then
    print_result 0 "Type Geometry ajouté dans gristTypes.ts"
else
    print_result 1 "Type Geometry manquant dans gristTypes.ts"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "'Vector'" app/common/gristTypes.ts; then
    print_result 0 "Type Vector ajouté dans gristTypes.ts"
else
    print_result 1 "Type Vector manquant dans gristTypes.ts"
    ERRORS=$((ERRORS + 1))
fi

# Vérifier widgets
if grep -q "GeometryEditor" app/client/widgets/UserTypeImpl.ts; then
    print_result 0 "GeometryEditor importé dans UserTypeImpl"
else
    print_result 1 "GeometryEditor manquant dans UserTypeImpl"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "VectorEditor" app/client/widgets/UserTypeImpl.ts; then
    print_result 0 "VectorEditor importé dans UserTypeImpl"
else
    print_result 1 "VectorEditor manquant dans UserTypeImpl"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "🧪 3. VALIDATION TESTS SYNTAXE"
echo "==============================="

# Vérifier syntaxe TypeScript (si tsc disponible)
if command -v tsc >/dev/null 2>&1; then
    print_info "Vérification syntaxe TypeScript..."
    if tsc --noEmit --skipLibCheck app/common/gristTypes.ts 2>/dev/null; then
        print_result 0 "Syntaxe gristTypes.ts valide"
    else
        print_result 1 "Erreurs de syntaxe dans gristTypes.ts"
        ERRORS=$((ERRORS + 1))
    fi
    
    if tsc --noEmit --skipLibCheck app/client/widgets/UserType.ts 2>/dev/null; then
        print_result 0 "Syntaxe UserType.ts valide"
    else
        print_result 1 "Erreurs de syntaxe dans UserType.ts"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_warning "TypeScript compiler non disponible - skip validation syntaxe"
    WARNINGS=$((WARNINGS + 1))
fi

# Vérifier syntaxe Python (si python disponible)
if command -v python3 >/dev/null 2>&1; then
    print_info "Vérification syntaxe Python..."
    if python3 -m py_compile sandbox/grist/usertypes.py 2>/dev/null; then
        print_result 0 "Syntaxe usertypes.py valide"
    else
        print_result 1 "Erreurs de syntaxe dans usertypes.py"
        ERRORS=$((ERRORS + 1))
    fi
    
    if python3 -m py_compile test/python/test_new_usertypes.py 2>/dev/null; then
        print_result 0 "Syntaxe test_new_usertypes.py valide"
    else
        print_result 1 "Erreurs de syntaxe dans test_new_usertypes.py"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_warning "Python non disponible - skip validation syntaxe"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "🐳 4. VALIDATION DOCKER SETUP"
echo "=============================="

if [ -f "docker-compose-examples/grist-postgis-pgvector/docker-compose-pgvector.yml" ]; then
    print_result 0 "Configuration Docker Compose présente"
    
    # Vérifier format YAML (si yq disponible)
    if command -v yq >/dev/null 2>&1; then
        if yq eval '.' docker-compose-examples/grist-postgis-pgvector/docker-compose-pgvector.yml >/dev/null 2>&1; then
            print_result 0 "Format YAML valide"
        else
            print_result 1 "Format YAML invalide"
            ERRORS=$((ERRORS + 1))
        fi
    else
        print_warning "yq non disponible - skip validation YAML"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_result 1 "Configuration Docker manquante"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "docker-compose-examples/grist-postgis-pgvector/init-extensions-pgvector.sql" ]; then
    print_result 0 "Script d'initialisation SQL présent"
else
    print_result 1 "Script d'initialisation SQL manquant"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "📚 5. VALIDATION DOCUMENTATION"
echo "==============================="

if [ -f "documentation/postgis-pgvector-support.md" ]; then
    doc_lines=$(wc -l < documentation/postgis-pgvector-support.md)
    if [ $doc_lines -gt 50 ]; then
        print_result 0 "Documentation technique complète ($doc_lines lignes)"
    else
        print_warning "Documentation technique courte ($doc_lines lignes)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_result 1 "Documentation technique manquante"
    ERRORS=$((ERRORS + 1))
fi

# Compter fichiers de documentation créés
doc_count=$(find docker-compose-examples/grist-postgis-pgvector/ -name "*.md" | wc -l)
if [ $doc_count -ge 3 ]; then
    print_result 0 "Documentation utilisateur complète ($doc_count fichiers)"
else
    print_warning "Documentation utilisateur limitée ($doc_count fichiers)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "📊 RÉSUMÉ VALIDATION"
echo "==================="

total_checks=$(($(grep -c "print_result" "$0") + WARNINGS))
success_checks=$((total_checks - ERRORS - WARNINGS))

echo -e "Total vérifications : ${BLUE}$total_checks${NC}"
echo -e "Succès : ${GREEN}$success_checks${NC}"
echo -e "Avertissements : ${YELLOW}$WARNINGS${NC}"
echo -e "Erreurs : ${RED}$ERRORS${NC}"

# Calculer score
if [ $total_checks -gt 0 ]; then
    score=$((success_checks * 100 / total_checks))
    echo -e "Score qualité : ${BLUE}$score%${NC}"
else
    score=0
fi

echo ""
echo "🎯 RECOMMANDATIONS FINALES"
echo "=========================="

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}🎉 PARFAIT ! Contribution prête pour submission upstream${NC}"
        echo -e "${GREEN}   Tous les composants sont implémentés correctement${NC}"
    else
        echo -e "${YELLOW}✅ TRÈS BON ! Quelques améliorations mineures suggérées${NC}"
        echo -e "${YELLOW}   Contribution acceptable pour submission${NC}"
    fi
else
    echo -e "${RED}❌ CORRECTIONS REQUISES avant submission${NC}"
    echo -e "${RED}   $ERRORS erreur(s) critique(s) à corriger${NC}"
fi

echo ""
if [ $score -ge 90 ]; then
    echo -e "${GREEN}🏆 QUALITÉ EXCEPTIONNELLE ($score/100)${NC}"
elif [ $score -ge 80 ]; then
    echo -e "${BLUE}👍 BONNE QUALITÉ ($score/100)${NC}"  
elif [ $score -ge 70 ]; then
    echo -e "${YELLOW}⚠️  QUALITÉ ACCEPTABLE ($score/100)${NC}"
else
    echo -e "${RED}💪 AMÉLIORATIONS NÉCESSAIRES ($score/100)${NC}"
fi

echo ""
echo "🚀 PROCHAINES ÉTAPES"
echo "==================="
echo "1. Corriger les erreurs identifiées"
echo "2. Exécuter les tests unitaires : yarn test:python && yarn test:client"
echo "3. Tester l'intégration Docker : docker-compose up"
echo "4. Préparer la Pull Request avec documentation impact"

# Exit avec code d'erreur approprié
if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi
