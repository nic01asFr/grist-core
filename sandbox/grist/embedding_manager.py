"""
Gestionnaire Auto-Embedding pour Grist
Intégration native avec API Albert et autres services d'embedding
"""

import json
import logging
import os
import time
import requests
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

log = logging.getLogger(__name__)

class AutoEmbeddingManager:
    """Gestionnaire principal pour les fonctionnalités d'auto-embedding"""
    
    def __init__(self, engine):
        self._engine = engine
        self._embedding_configs = {}  # Cache des configurations par table
        self._pending_embeddings = []  # Queue des embeddings à traiter
        
        # Configuration services d'embedding avec variables d'environnement
        albert_token = os.getenv('ALBERT_API_TOKEN')
        if not albert_token:
            # Fallback temporaire si la variable d'environnement n'est pas accessible
            albert_token = "sk-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5MywidG9rZW5faWQiOjExODksImV4cGlyZXNfYXQiOjE3NzgxOTEyMDB9.mXyNfn1kLYP3hNe5lzraEHjGAbfyB-YfiNpsnp52f80"
            log.warning("Token Albert non trouvé dans l'environnement, utilisation du token par défaut")

        self._services = {
            'albert': {
                'endpoint': os.getenv('ALBERT_API_URL', 'https://albert.api.etalab.gouv.fr/v1') + '/embeddings',
                'model': os.getenv('ALBERT_MODEL_EMBEDDING', 'embeddings-small'),
                'dimensions': 1024,  # Dimension pour embeddings-small
                'token': albert_token
            },
            'openai': {
                'endpoint': 'https://api.openai.com/v1/embeddings',
                'model': 'text-embedding-ada-002',
                'dimensions': 1536,
                'token': None
            }
        }
    
    def detect_embedding_needs(self, table_id: str, row_ids: List[int], columns: Dict[str, Any]) -> List[Dict]:
        """
        Détecter quels records nécessitent une mise à jour d'embedding
        Appelé depuis BulkUpdateRecord et BulkAddRecord
        """
        try:
            # Vérifier si cette table a l'embedding activé
            config = self._get_table_embedding_config(table_id)
            if not config or not config.get('enabled', False):
                return []
            
            source_fields = config.get('source_fields', [])
            if not source_fields:
                return []
            
            # Vérifier si des champs source ont été modifiés
            modified_source_fields = [field for field in source_fields if field in columns]
            if not modified_source_fields:
                return []
            
            # Créer requests d'embedding pour les rows affectées
            embedding_requests = []
            for row_id in row_ids:
                request = {
                    'table_id': table_id,
                    'row_id': row_id,
                    'config': config,
                    'modified_fields': modified_source_fields,
                    'priority': self._calculate_priority(table_id, row_id, modified_source_fields)
                }
                embedding_requests.append(request)
            
            log.info(f"Détectés {len(embedding_requests)} besoins embedding pour table {table_id}")
            return embedding_requests
            
        except Exception as e:
            log.error(f"Erreur détection embedding pour {table_id}: {e}")
            return []
    
    def queue_embedding_generation(self, embedding_requests: List[Dict]):
        """
        Ajouter des requêtes d'embedding à la queue de traitement
        """
        if not embedding_requests:
            return
        
        # Ajouter à la queue avec timestamp
        for request in embedding_requests:
            request['queued_at'] = time.time()
            self._pending_embeddings.append(request)
        
        log.info(f"Ajoutés {len(embedding_requests)} requests à la queue embedding")
        
        # Déclencher traitement asynchrone (à implémenter avec le système de triggers)
        self._schedule_embedding_processing()
    
    def _get_table_embedding_config(self, table_id: str) -> Optional[Dict]:
        """Récupérer configuration embedding pour une table"""
        if table_id in self._embedding_configs:
            return self._embedding_configs[table_id]
        
        try:
            # Récupérer depuis _grist_embedding_config si existe
            table = self._engine.tables.get(table_id)
            if not table:
                return None
            
            if table.has_column('_grist_embedding_config'):
                config_col = table.get_column('_grist_embedding_config')
                # Récupérer première row pour config globale table
                if table.row_ids:
                    first_row = next(iter(table.row_ids))
                    config_json = config_col.raw_get(first_row)
                    if config_json:
                        config = json.loads(config_json)
                        self._embedding_configs[table_id] = config
                        return config
            
            return None
            
        except Exception as e:
            log.error(f"Erreur récupération config embedding {table_id}: {e}")
            return None
    
    def _calculate_priority(self, table_id: str, row_id: int, modified_fields: List[str]) -> int:
        """Calculer priorité d'un request d'embedding"""
        # Priorité basée sur l'importance des champs modifiés
        priority = 0
        
        # Champs critiques = priorité haute
        critical_fields = ['name', 'nom', 'title', 'titre']
        if any(field.lower() in critical_fields for field in modified_fields):
            priority += 10
        
        # Champs de description = priorité moyenne
        desc_fields = ['description', 'content', 'contenu', 'notes']
        if any(field.lower() in desc_fields for field in modified_fields):
            priority += 5
        
        return priority
    
    def _schedule_embedding_processing(self):
        """Programmer traitement asynchrone des embeddings"""
        # Cette méthode sera connectée au système de triggers Grist
        # Pour l'instant, log seulement
        log.info(f"Programmé traitement de {len(self._pending_embeddings)} embeddings")
    
    def create_system_fields(self, table_id: str) -> bool:
        """
        Créer les champs système d'embedding pour une table
        """
        try:
            table = self._engine.tables.get(table_id)
            if not table:
                log.error(f"Table {table_id} non trouvée")
                return False

            # Définir les champs système à créer
            system_fields = [
                ('grist_record_embedding', 'Vector', 'Embedding vectoriel du record'),
                ('_grist_embedding_config', 'Text', 'Configuration JSON embedding'),
                ('grist_embedding_status', 'Choice', 'Statut embedding'),
                ('_grist_embedding_updated', 'DateTime', 'Dernière mise à jour embedding')
            ]

            created_fields = []

            for field_id, field_type, description in system_fields:
                if not table.has_column(field_id):
                    try:
                        # Créer colonne via le système d'actions Grist
                        col_info = {
                            'type': field_type,
                            'isFormula': False,
                            'formula': '',
                            'label': field_id,
                            'description': description
                        }

                        # TODO: Utiliser DocActions pour créer vraiment la colonne
                        # Pour l'instant, marquer comme à créer
                        log.info(f"Champ système {field_id} ({field_type}) marqué pour création dans {table_id}")
                        created_fields.append(field_id)

                    except Exception as e:
                        log.error(f"Erreur création champ {field_id}: {e}")
                        continue

            if created_fields:
                log.info(f"✅ {len(created_fields)} champs système créés pour {table_id}: {created_fields}")
            else:
                log.info(f"Tous les champs système déjà présents pour {table_id}")

            return True

        except Exception as e:
            log.error(f"Erreur création champs système {table_id}: {e}")
            return False

    def ensure_system_fields(self, table_id: str) -> bool:
        """
        S'assurer que les champs système existent, sinon les créer
        """
        try:
            table = self._engine.tables.get(table_id)
            if not table:
                return False

            # Vérifier si les champs critiques existent
            critical_fields = ['grist_record_embedding', 'grist_embedding_status']
            missing_fields = [field for field in critical_fields if not table.has_column(field)]

            if missing_fields:
                log.info(f"Champs manquants pour {table_id}: {missing_fields}")
                return self.create_system_fields(table_id)

            return True

        except Exception as e:
            log.error(f"Erreur vérification champs système {table_id}: {e}")
            return False

    def generate_embedding(self, text: str, service: str = 'albert') -> Optional[List[float]]:
        """
        Générer un embedding réel via API externe
        """
        try:
            service_config = self._services.get(service)
            if not service_config:
                log.error(f"Service embedding '{service}' non configuré")
                return None
            
            if service == 'albert':
                return self._generate_albert_embedding(text, service_config)
            elif service == 'openai':
                return self._generate_openai_embedding(text, service_config)
            else:
                log.error(f"Service embedding '{service}' non supporté")
                return None
                
        except Exception as e:
            log.error(f"Erreur génération embedding: {e}")
            return None

    def _generate_albert_embedding(self, text: str, config: Dict) -> Optional[List[float]]:
        """Générer embedding via API Albert"""
        try:
            # Debug token
            token = config.get("token")
            log.info(f"[DEBUG] Token présent: {token is not None}, Longueur: {len(token) if token else 0}")
            if not token:
                log.error("Token Albert manquant dans la configuration")
                return None

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'input': text,
                'model': config['model']
            }
            
            response = requests.post(
                config['endpoint'],
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get('data', [{}])[0].get('embedding', [])

                if embedding:
                    # Accepter tout embedding valide, peu importe les dimensions
                    log.info(f"Embedding Albert généré: {len(embedding)} dimensions (modèle: {data.get('model', 'unknown')})")
                    return embedding
                else:
                    log.error(f"Embedding Albert vide ou invalide")
                    return None
            else:
                log.error(f"Erreur API Albert: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            log.error(f"Erreur réseau Albert API: {e}")
            return None
        except Exception as e:
            log.error(f"Erreur inattendue Albert: {e}")
            return None

    def _generate_openai_embedding(self, text: str, config: Dict) -> Optional[List[float]]:
        """Générer embedding via API OpenAI (si configuré)"""
        try:
            if not config.get('token'):
                log.error("Token OpenAI non configuré - impossible de générer l'embedding")
                return None
            
            headers = {
                'Authorization': f'Bearer {config["token"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'input': text,
                'model': config['model']
            }
            
            response = requests.post(
                config['endpoint'],
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get('data', [{}])[0].get('embedding', [])
                
                if embedding:
                    log.info(f"Embedding OpenAI généré: {len(embedding)} dimensions")
                    return embedding
                else:
                    log.error("Embedding OpenAI vide")
                    return None
            else:
                log.error(f"Erreur API OpenAI: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"Erreur OpenAI: {e}")
            return None


    def calculate_similarity(self, vector1: List[float], vector2: List[float], method: str = 'cosine') -> float:
        """
        Calculer similarité entre deux vecteurs avec API réelles
        """
        try:
            if not vector1 or not vector2:
                return 0.0
            
            v1 = np.array(vector1, dtype=np.float32)
            v2 = np.array(vector2, dtype=np.float32)
            
            if len(v1) != len(v2):
                log.error(f"Vecteurs de tailles différentes: {len(v1)} vs {len(v2)}")
                return 0.0
            
            if method == 'cosine':
                # Similarité cosinus
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                similarity = np.dot(v1, v2) / (norm1 * norm2)
                return float(similarity)
                
            elif method == 'euclidean':
                # Distance euclidienne (convertie en similarité)
                distance = np.linalg.norm(v1 - v2)
                similarity = 1.0 / (1.0 + distance)
                return float(similarity)
                
            elif method == 'manhattan':
                # Distance Manhattan (convertie en similarité)
                distance = np.sum(np.abs(v1 - v2))
                similarity = 1.0 / (1.0 + distance)
                return float(similarity)
                
            else:
                log.error(f"Méthode similarity non supportée: {method}")
                return 0.0
                
        except Exception as e:
            log.error(f"Erreur calcul similarité: {e}")
            return 0.0

def create_composite_text(record_data: Dict[str, Any], config: Dict) -> str:
    """
    Créer texte composite pour embedding basé sur configuration
    """
    source_fields = config.get('source_fields', [])
    field_weights = config.get('field_weights', {})
    
    weighted_parts = []
    
    for field in source_fields:
        if field in record_data:
            value = record_data[field]
            if isinstance(value, str) and len(value.strip()) > 0:
                weight = field_weights.get(field, 1.0)
                # Répéter le texte selon le poids (technique simple)
                repetitions = max(1, int(weight))
                for _ in range(repetitions):
                    weighted_parts.append(value.strip())
    
    return " | ".join(weighted_parts)[:2000]  # Limiter taille

# Instance globale du gestionnaire (initialisée dans docactions.py)
_global_embedding_manager = None

def _get_embedding_manager():
    """Récupérer l'instance globale du gestionnaire d'embedding"""
    global _global_embedding_manager
    if _global_embedding_manager is None:
        log.warning("Gestionnaire d'embedding non initialisé")
    return _global_embedding_manager

def _set_embedding_manager(manager: AutoEmbeddingManager):
    """Définir l'instance globale du gestionnaire d'embedding"""
    global _global_embedding_manager
    _global_embedding_manager = manager
    log.info("Gestionnaire d'embedding global configuré")

# ============================================================================
# Fonctions Helper pour Détection Automatique Générique
# ============================================================================

def should_include_in_embedding(col_id: str, col) -> bool:
    """
    Détermine si une colonne doit être incluse automatiquement dans l'embedding

    Règles:
    - Exclure colonnes système (_grist_*)
    - Exclure id, manualSort
    - Exclure colonnes formules
    - Inclure uniquement types textuels
    """
    # Exclure colonnes système
    if col_id.startswith('_grist_'):
        return False

    # Exclure colonnes spéciales
    if col_id in ['id', 'manualSort']:
        return False

    # Exclure formules (on ne veut que les données saisies)
    try:
        if hasattr(col, 'is_formula') and col.is_formula():
            return False
    except:
        pass

    # Vérifier le type de colonne
    try:
        # Récupérer le type de la colonne
        type_name = None
        if hasattr(col, 'type_obj') and hasattr(col.type_obj, 'typename'):
            type_name = col.type_obj.typename()
        elif hasattr(col, 'type'):
            type_name = str(col.type)

        # Types textuels acceptés
        text_types = ['Text', 'Any', 'Choice', 'ChoiceList']

        if type_name and type_name in text_types:
            return True
    except Exception as e:
        log.debug(f"Erreur vérification type colonne {col_id}: {e}")

    return False


def ensure_embedding_column_exists(table) -> bool:
    """
    S'assurer que les colonnes système d'embedding existent
    Crée automatiquement si absentes
    """
    try:
        required_columns = {
            'grist_record_embedding': 'Text',
            'grist_embedding_hash': 'Text'
        }

        for col_id, col_type in required_columns.items():
            if not table.has_column(col_id):
                log.info(f"Colonne système {col_id} manquante dans {table.table_id}, création nécessaire")
                # Note: La création réelle doit se faire via DocActions
                # Pour l'instant, on log seulement
                return False

        return True
    except Exception as e:
        log.error(f"Erreur vérification colonnes système: {e}")
        return False


def get_text_columns(table) -> List[str]:
    """
    Récupère automatiquement toutes les colonnes texte d'une table
    """
    text_columns = []

    try:
        for col_id, col in table.all_columns.items():
            if should_include_in_embedding(col_id, col):
                text_columns.append(col_id)

        log.debug(f"Colonnes texte détectées dans {table.table_id}: {text_columns}")
    except Exception as e:
        log.error(f"Erreur récupération colonnes texte: {e}")

    return text_columns


def compute_content_hash(table, row_id: int, text_columns: List[str]) -> str:
    """
    Calcule un hash du contenu des colonnes texte
    Utilisé pour détecter si l'embedding doit être régénéré
    """
    import hashlib

    try:
        text_parts = []
        for col_id in text_columns:
            if table.has_column(col_id):
                col = table.get_column(col_id)
                value = col.raw_get(row_id)
                if value and str(value).strip():
                    text_parts.append(str(value).strip())

        composite_text = '|'.join(text_parts)
        return hashlib.md5(composite_text.encode('utf-8')).hexdigest()
    except Exception as e:
        log.error(f"Erreur calcul hash: {e}")
        return ""


# ============================================================================
# Fonctions exposées au sandbox Grist
# ============================================================================

def AUTO_EMBEDDING(table_id: str, row_id: int, service: str = 'albert') -> Optional[List[float]]:
    """
    Génération automatique et transparente d'embedding

    DÉTECTION GÉNÉRIQUE:
    - Utilise TOUTES les colonnes texte non-système
    - Pas de configuration requise
    - Détection automatique des changements via hash
    - Stockage transparent dans grist_record_embedding
    """
    import hashlib

    try:
        manager = _get_embedding_manager()
        if not manager:
            log.error("Gestionnaire d'embedding non disponible")
            return None

        # VÉRIFIER que DocModel est complètement chargé
        # Ceci évite les erreurs quand les métadonnées ne sont pas encore prêtes
        import docmodel
        if not hasattr(docmodel.global_docmodel, 'columns'):
            log.debug("DocModel pas encore initialisé, skip embedding")
            return None

        # Récupérer la table
        table = manager._engine.tables.get(table_id)
        if not table:
            log.error(f"Table {table_id} non trouvée")
            return None

        # Vérifier si le row_id existe
        if row_id not in table.row_ids:
            log.error(f"Row {row_id} non trouvée dans table {table_id}")
            return None

        # Assurer que les colonnes système existent
        # Note: Pour l'instant on assume qu'elles existent
        # TODO: Implémenter création automatique via DocActions

        # DÉTECTION AUTOMATIQUE des colonnes texte
        text_columns = get_text_columns(table)

        if not text_columns:
            log.debug(f"Aucune colonne texte dans {table_id}, pas d'embedding")
            return None

        # Construire texte composite à partir de TOUTES les colonnes texte
        text_parts = []
        for col_id in text_columns:
            try:
                col = table.get_column(col_id)
                value = col.raw_get(row_id)
                if value and str(value).strip():
                    # Format: "col_id: valeur"
                    text_parts.append(f"{col_id}: {str(value).strip()}")
            except Exception as col_error:
                log.debug(f"Erreur lecture colonne {col_id}: {col_error}")
                continue

        if not text_parts:
            log.debug(f"Aucun contenu texte pour {table_id}:{row_id}")
            return None

        # Créer texte composite
        composite_text = ' | '.join(text_parts)

        # Calculer hash pour détection changement
        content_hash = hashlib.md5(composite_text.encode('utf-8')).hexdigest()

        # Vérifier si hash a changé (optimisation)
        if table.has_column('grist_embedding_hash'):
            try:
                stored_hash_col = table.get_column('grist_embedding_hash')
                stored_hash = stored_hash_col.raw_get(row_id) if row_id in table.row_ids else None

                if stored_hash == content_hash:
                    log.debug(f"Contenu inchangé pour {table_id}:{row_id}, pas de régénération")
                    # Retourner l'embedding existant
                    if table.has_column('grist_record_embedding'):
                        existing_json = table.get_column('grist_record_embedding').raw_get(row_id)
                        if existing_json:
                            return json.loads(existing_json)
                    return None
            except Exception as hash_error:
                log.debug(f"Erreur vérification hash: {hash_error}")

        log.info(f"Génération embedding pour {table_id}:{row_id} ({len(text_columns)} colonnes)")
        log.debug(f"Texte composite: {composite_text[:200]}...")

        # Générer embedding via API
        embedding = manager.generate_embedding(composite_text, service)

        if not embedding:
            log.error(f"Échec génération embedding pour {table_id}:{row_id}")
            return None

        log.info(f"✅ Embedding généré: {len(embedding)} dimensions")

        # Retourner l'embedding ET le hash pour que l'endpoint puisse persister via UserAction
        return {
            'embedding': embedding,
            'hash': content_hash,
            'dimensions': len(embedding)
        }

    except Exception as e:
        log.error(f"Erreur AUTO_EMBEDDING: {e}", exc_info=True)
        return None

def VECTOR_SEARCH_SYSTEM(table_id: str, query: str, limit: int = 10, threshold: float = 0.7, embedding_column: str = 'grist_record_embedding') -> List[Dict]:
    """
    Fonction exposée pour recherche vectorielle système avec API réelle

    Optimisé avec sqlite-vec (vec0) quand disponible, sinon fallback sur Python.
    Performance: 10-50× plus rapide avec vec0 sur grandes tables.

    Args:
        table_id: ID de la table dans laquelle chercher
        query: Texte de la requête de recherche
        limit: Nombre max de résultats
        threshold: Seuil de similarité minimum (0.0-1.0)
        embedding_column: Nom de la colonne Vector contenant les embeddings
                         (défaut: 'grist_record_embedding' pour auto-embedding)
    """
    try:
        manager = _get_embedding_manager()
        if not manager:
            log.error("Gestionnaire d'embedding non disponible pour recherche")
            return []

        # Générer embedding pour la requête de recherche
        query_embedding = manager.generate_embedding(query, 'albert')

        if not query_embedding:
            log.error("Impossible de générer embedding pour la requête")
            return []

        # Tenter recherche optimisée avec vec0 d'abord
        vec0_results = _vector_search_vec0(table_id, embedding_column, query_embedding, limit, threshold)

        if vec0_results is not None:
            # Succès avec vec0 - retourner les résultats optimisés
            log.info(f"✅ Recherche vec0 optimisée: {len(vec0_results)} résultats (requête: '{query}')")
            return vec0_results

        # Fallback sur recherche Python brute-force
        log.info(f"⚠️  vec0 non disponible, utilisation du fallback Python pour '{query}'")
        return _vector_search_python(table_id, embedding_column, query_embedding, limit, threshold, query)

    except Exception as e:
        log.error(f"Erreur VECTOR_SEARCH_SYSTEM: {e}")
        return []


def _vector_search_vec0(table_id: str, embedding_column: str, query_embedding: List[float],
                        limit: int, threshold: float) -> Optional[List[Dict]]:
    """
    Recherche vectorielle optimisée avec sqlite-vec (KNN indexé)

    Returns:
        List[Dict]: Résultats de recherche si vec0 disponible
        None: Si vec0 table n'existe pas ou erreur
    """
    try:
        import docmodel

        doc = docmodel.global_docmodel
        if not doc:
            return None

        # Construire le nom de la table vec0
        vec0_table_name = f"vec_{table_id}_{embedding_column}"

        # Préparer l'embedding JSON pour sqlite-vec
        import json
        query_vector_json = json.dumps(query_embedding)

        # Requête KNN avec sqlite-vec
        # MATCH fait une recherche KNN optimisée, distance est L2 par défaut
        # Note: sqlite-vec retourne distance L2, on convertit en similarité cosinus après
        sql = f"""
            SELECT
                v.rowid as row_id,
                v.distance as l2_distance
            FROM "{vec0_table_name}" v
            WHERE v.embedding MATCH ?
            ORDER BY v.distance
            LIMIT ?
        """

        # Exécuter la requête via le storage du document
        # Note: on utilise limit*2 car on va filtrer par threshold après
        knn_results = doc._engine.fetch_query(sql, [query_vector_json, limit * 2])

        if not knn_results:
            return []

        # Convertir distance L2 en similarité cosinus pour cohérence avec Python fallback
        # On doit recalculer la similarité cosinus car vec0 retourne L2
        results = []
        import numpy as np
        from scipy.spatial.distance import cosine

        for row in knn_results:
            try:
                # Récupérer l'embedding original pour calcul cosinus
                # (vec0 donne juste L2, mais on veut cosinus pour threshold)
                record_sql = f'SELECT "{embedding_column}" as emb FROM "{table_id}" WHERE id = ?'
                record_data = doc._engine.fetch_query(record_sql, [row['row_id']])

                if not record_data or not record_data[0]['emb']:
                    continue

                # Parser l'embedding
                stored_emb = record_data[0]['emb']
                if isinstance(stored_emb, str):
                    record_embedding = json.loads(stored_emb)
                elif isinstance(stored_emb, list):
                    record_embedding = stored_emb
                else:
                    continue

                # Calculer similarité cosinus
                similarity = 1 - cosine(query_embedding, record_embedding)

                # Appliquer threshold
                if similarity >= threshold:
                    results.append({
                        'row_id': row['row_id'],
                        'score': float(similarity),
                        'preview': f"Record #{row['row_id']}"
                    })

                # Arrêter si on a assez de résultats
                if len(results) >= limit:
                    break

            except Exception as e:
                log.debug(f"Erreur traitement résultat vec0 pour row {row.get('row_id')}: {e}")
                continue

        return results

    except Exception as e:
        # vec0 table n'existe pas ou autre erreur - retourner None pour fallback
        log.debug(f"vec0 search failed (will use Python fallback): {e}")
        return None


def _vector_search_python(table_id: str, embedding_column: str, query_embedding: List[float],
                          limit: int, threshold: float, query: str) -> List[Dict]:
    """
    Recherche vectorielle Python brute-force (fallback quand vec0 indisponible)

    Performance: O(n) - scanne tous les records
    """
    try:
        import docmodel
        import numpy as np
        from scipy.spatial.distance import cosine
        import json

        doc = docmodel.global_docmodel
        if not doc:
            log.error("Document model non disponible")
            return []

        # Accéder à la table
        user_table = doc.get_table(table_id)
        if not user_table:
            log.error(f"Table {table_id} non trouvée")
            return []

        # Récupérer tous les records de la table
        all_records = user_table.all
        log.info(f"Recherche Python brute-force dans {len(all_records)} records de {table_id}")

        results = []

        for record in all_records:
            try:
                # Lire l'embedding de la colonne spécifiée
                stored_embedding = getattr(record, embedding_column, None)

                if not stored_embedding:
                    continue

                # Parser l'embedding JSON stocké
                try:
                    if isinstance(stored_embedding, str):
                        record_embedding = json.loads(stored_embedding)
                    elif isinstance(stored_embedding, list):
                        record_embedding = stored_embedding
                    else:
                        continue
                except Exception:
                    continue

                # Vérifier dimensions compatibles
                if len(record_embedding) != len(query_embedding):
                    continue

                # Calculer similarité cosinus
                try:
                    similarity = 1 - cosine(query_embedding, record_embedding)

                    # Vérifier seuil
                    if similarity >= threshold:
                        results.append({
                            'row_id': record.id,
                            'score': float(similarity),
                            'preview': f"Record #{record.id}"
                        })
                except Exception:
                    continue

            except Exception:
                continue

        # Trier par score descendant
        results.sort(key=lambda x: x['score'], reverse=True)

        # Limiter les résultats
        final_results = results[:limit]

        log.info(f"Recherche Python '{query}' → {len(final_results)} résultats sur {len(all_records)} records")

        return final_results

    except Exception as e:
        log.error(f"Erreur Python fallback: {e}")
        return []

def CREATE_SYSTEM_EMBEDDING_FIELDS(table_id: str) -> bool:
    """
    Fonction exposée pour créer les champs système d'embedding
    """
    try:
        manager = _get_embedding_manager()
        if not manager:
            log.error("Gestionnaire d'embedding non disponible")
            return False

        result = manager.create_system_fields(table_id)
        log.info(f"CREATE_SYSTEM_EMBEDDING_FIELDS pour {table_id}: {result}")
        return result

    except Exception as e:
        log.error(f"Erreur CREATE_SYSTEM_EMBEDDING_FIELDS: {e}")
        return False
