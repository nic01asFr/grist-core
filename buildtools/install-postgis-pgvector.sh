#!/bin/bash
set -e

# Script d'installation des extensions PostGIS et pg_vector pour Grist
# Usage: ./install-postgis-pgvector.sh [--help]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions d'affichage
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Installation des extensions PostGIS et pg_vector pour Grist

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Afficher cette aide
    --check-only           Vérifier seulement si les extensions sont supportées
    --postgres-only        Installer seulement PostGIS (ignorer pg_vector)
    --skip-migration       Ne pas exécuter la migration automatiquement

DESCRIPTION:
    Ce script vérifie et installe les dépendances nécessaires pour le support
    des extensions PostGIS (données spatiales) et pg_vector (embeddings) dans Grist.

EXEMPLES:
    $0                     # Installation complète
    $0 --check-only        # Vérification seulement
    $0 --postgres-only     # PostGIS seulement

Pour plus d'informations, voir: documentation/postgis-pgvector-support.md
EOF
}

# Parser les arguments
CHECK_ONLY=false
POSTGRES_ONLY=false
SKIP_MIGRATION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --postgres-only)
            POSTGRES_ONLY=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Vérifier si on est dans un projet Grist
if [ ! -f "$PROJECT_ROOT/package.json" ] || ! grep -q "grist" "$PROJECT_ROOT/package.json"; then
    log_error "Ce script doit être exécuté depuis le répertoire racine de Grist"
    exit 1
fi

log_info "🚀 Installation des extensions PostGIS et pg_vector pour Grist"
echo

# Détecter l'OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
log_info "Système détecté: $OS"

# Vérifier PostgreSQL
check_postgresql() {
    log_info "Vérification de PostgreSQL..."
    
    if ! command -v pg_config &> /dev/null; then
        log_error "pg_config introuvable. PostgreSQL development packages requis."
        
        case $OS in
            debian)
                log_info "Installation recommandée: sudo apt-get install postgresql-server-dev-all"
                ;;
            redhat)
                log_info "Installation recommandée: sudo yum install postgresql-devel"
                ;;
            macos)
                log_info "Installation recommandée: brew install postgresql"
                ;;
        esac
        return 1
    fi
    
    PG_VERSION=$(pg_config --version | awk '{print $2}' | cut -d. -f1)
    log_success "PostgreSQL $PG_VERSION détecté"
    return 0
}

# Installer PostGIS
install_postgis() {
    log_info "Vérification de PostGIS..."
    
    case $OS in
        debian)
            if ! dpkg -l | grep -q postgresql.*postgis; then
                log_info "Installation de PostGIS..."
                sudo apt-get update
                sudo apt-get install -y "postgresql-$PG_VERSION-postgis-3"
            else
                log_success "PostGIS déjà installé"
            fi
            ;;
        redhat)
            if ! rpm -qa | grep -q postgis; then
                log_info "Installation de PostGIS..."
                sudo yum install -y "postgis34_$PG_VERSION"
            else
                log_success "PostGIS déjà installé"
            fi
            ;;
        macos)
            if ! brew list | grep -q postgis; then
                log_info "Installation de PostGIS..."
                brew install postgis
            else
                log_success "PostGIS déjà installé"
            fi
            ;;
        *)
            log_warning "Installation automatique de PostGIS non supportée sur $OS"
            log_info "Veuillez installer PostGIS manuellement selon votre distribution"
            return 1
            ;;
    esac
    
    return 0
}

# Installer pg_vector
install_pgvector() {
    if [ "$POSTGRES_ONLY" = true ]; then
        log_info "Ignorer pg_vector (--postgres-only spécifié)"
        return 0
    fi
    
    log_info "Vérification de pg_vector..."
    
    # Vérifier si déjà installé
    PG_LIB_DIR=$(pg_config --pkglibdir)
    if [ -f "$PG_LIB_DIR/vector.so" ]; then
        log_success "pg_vector déjà installé"
        return 0
    fi
    
    # Installer les dépendances de build
    case $OS in
        debian)
            log_info "Installation des dépendances de build..."
            sudo apt-get install -y git build-essential
            ;;
        redhat)
            log_info "Installation des dépendances de build..."
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y git
            ;;
        macos)
            if ! command -v git &> /dev/null; then
                log_info "Installation de git..."
                brew install git
            fi
            ;;
    esac
    
    # Compiler et installer pg_vector
    log_info "Compilation et installation de pg_vector..."
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    git clone https://github.com/pgvector/pgvector.git
    cd pgvector
    
    make clean || true
    make
    sudo make install
    
    cd "$PROJECT_ROOT"
    rm -rf "$TEMP_DIR"
    
    log_success "pg_vector installé avec succès"
    return 0
}

# Tester les extensions
test_extensions() {
    log_info "Test des extensions avec PostgreSQL..."
    
    # Cette partie nécessiterait une connexion à une base PostgreSQL
    # Pour l'instant, on vérifie juste la présence des fichiers
    
    PG_SHARE_DIR=$(pg_config --sharedir)
    PG_LIB_DIR=$(pg_config --pkglibdir)
    
    # Test PostGIS
    if [ -f "$PG_SHARE_DIR/extension/postgis.control" ]; then
        log_success "PostGIS prêt"
    else
        log_error "PostGIS non trouvé"
        return 1
    fi
    
    # Test pg_vector
    if [ "$POSTGRES_ONLY" = false ]; then
        if [ -f "$PG_SHARE_DIR/extension/vector.control" ]; then
            log_success "pg_vector prêt"
        else
            log_error "pg_vector non trouvé"
            return 1
        fi
    fi
    
    return 0
}

# Exécuter la migration
run_migration() {
    if [ "$SKIP_MIGRATION" = true ]; then
        log_info "Migration ignorée (--skip-migration spécifié)"
        return 0
    fi
    
    log_info "Exécution de la migration PostgreSQL..."
    
    # Vérifier si Node.js et npm sont disponibles
    if ! command -v npm &> /dev/null; then
        log_warning "npm non trouvé. Migration manuelle requise."
        log_info "Exécutez: npm run typeorm migration:run"
        return 1
    fi
    
    # Exécuter la migration
    if npm run typeorm migration:run; then
        log_success "Migration exécutée avec succès"
    else
        log_error "Échec de la migration"
        log_info "Vous pouvez l'exécuter manuellement avec: npm run typeorm migration:run"
        return 1
    fi
    
    return 0
}

# Fonction principale
main() {
    # Vérifications préliminaires
    if ! check_postgresql; then
        exit 1
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        log_info "Mode vérification seulement"
        if test_extensions; then
            log_success "Toutes les extensions sont disponibles"
            exit 0
        else
            log_error "Extensions manquantes"
            exit 1
        fi
    fi
    
    # Installation
    log_info "Début de l'installation..."
    
    if ! install_postgis; then
        log_error "Échec de l'installation de PostGIS"
        exit 1
    fi
    
    if ! install_pgvector; then
        log_error "Échec de l'installation de pg_vector"
        exit 1
    fi
    
    # Tests
    if ! test_extensions; then
        log_error "Tests des extensions échoués"
        exit 1
    fi
    
    # Migration
    if ! run_migration; then
        log_warning "Migration non exécutée automatiquement"
    fi
    
    log_success "🎉 Installation terminée avec succès!"
    echo
    log_info "Prochaines étapes:"
    log_info "1. Démarrer votre base PostgreSQL avec les nouvelles extensions"
    log_info "2. Configurer Grist avec TYPEORM_TYPE=postgres"
    log_info "3. Créer des colonnes de type 'Geometry' et 'Vector'"
    echo
    log_info "Documentation: $PROJECT_ROOT/documentation/postgis-pgvector-support.md"
}

# Exécuter le script principal
main "$@"
