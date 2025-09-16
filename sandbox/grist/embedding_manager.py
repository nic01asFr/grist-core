"""
Gestionnaire Auto-Embedding pour Grist
Intégration native avec API Albert et autres services d'embedding
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple

log = logging.getLogger(__name__)

class AutoEmbeddingManager:
    """Gestionnaire principal pour les fonctionnalités d'auto-embedding"""
    
    def __init__(self, engine):
        self._engine = engine
        self._embedding_configs = {}  # Cache des configurations par table
        self._pending_embeddings = []  # Queue des embeddings à traiter
        
        # Configuration services d'embedding
        self._services = {
            'albert': {
                'endpoint': 'https://albert.api.etalab.gouv.fr/v1/embeddings',
                'model': 'embeddings-small',
                'dimensions': 1024,
                'token': None  # À configurer via variables d'environnement
            },
            'openai': {
                'endpoint': 'https://api.openai.com/v1/embeddings',
                'model': 'text-embedding-ada-002',
                'dimensions': 1536,
                'token': None
            },
            'mock': {
                'endpoint': None,
                'model': 'mock-embedding',
                'dimensions': 8,
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
            
            log.info(f"✅ Détectés {len(embedding_requests)} besoins embedding pour table {table_id}")
            return embedding_requests
            
        except Exception as e:
            log.error(f"❌ Erreur détection embedding pour {table_id}: {e}")
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
        
        log.info(f"📝 Ajoutés {len(embedding_requests)} requests à la queue embedding")
        
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
            log.error(f"❌ Erreur récupération config embedding {table_id}: {e}")
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
        log.info(f"⏰ Programmé traitement de {len(self._pending_embeddings)} embeddings")
    
    def create_system_fields(self, table_id: str) -> bool:
        """
        Créer les champs système d'embedding pour une table
        """
        try:
            table = self._engine.tables.get(table_id)
            if not table:
                log.error(f"❌ Table {table_id} non trouvée")
                return False
            
            # Vérifier si les champs existent déjà
            system_fields = [
                '_grist_record_embedding',
                '_grist_embedding_config', 
                '_grist_embedding_status',
                '_grist_embedding_updated'
            ]
            
            existing_fields = [field for field in system_fields if table.has_column(field)]
            if len(existing_fields) == len(system_fields):
                log.info(f"✅ Champs système déjà présents pour {table_id}")
                return True
            
            # Créer les champs manquants via actions (à implémenter avec DocActions)
            log.info(f"🏗️ Création champs système pour {table_id}")
            return True
            
        except Exception as e:
            log.error(f"❌ Erreur création champs système {table_id}: {e}")
            return False

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

# Fonctions exposées au sandbox Grist
def AUTO_EMBEDDING(table_id: str, row_id: int) -> Optional[List[float]]:
    """
    Fonction exposée pour génération automatique d'embedding
    """
    # Cette fonction sera appelée par les formules Grist
    # Implémentation à compléter avec accès au EmbeddingManager
    return None

def VECTOR_SEARCH_SYSTEM(table_id: str, query: str, limit: int = 10, threshold: float = 0.7) -> List[Dict]:
    """
    Fonction exposée pour recherche vectorielle système
    """
    # Cette fonction sera appelée par les formules Grist et API
    return []
