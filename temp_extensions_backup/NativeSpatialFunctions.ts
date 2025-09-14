/**
 * Fonctions natives Grist pour les fonctionnalités spatiales et vectorielles
 * Intégration directe avec les formules Grist
 */

import { spatialVectorService } from './SpatialVectorService';
import { log } from './log';

/**
 * Collection de fonctions natives pour l'intégration spatiale et vectorielle
 * Ces fonctions sont directement utilisables dans les formules Grist
 */

// ============================================================================
// FONCTIONS VECTORIELLES NATIVES
// ============================================================================

/**
 * Génère un embedding pour un texte donné
 * Utilisation: GENERATE_EMBEDDING("Mon texte à analyser")
 */
export async function GENERATE_EMBEDDING(text: string): Promise<number[]> {
  if (typeof text !== 'string') {
    throw new Error('GENERATE_EMBEDDING: Le paramètre doit être une chaîne de caractères');
  }
  
  try {
    return await spatialVectorService.generateEmbedding(text);
  } catch (error) {
    log.error('GENERATE_EMBEDDING error:', error);
    throw new Error(`GENERATE_EMBEDDING: ${error.message}`);
  }
}

/**
 * Recherche de textes similaires basée sur l'embedding
 * Utilisation: SEARCH_SIMILAR("texte de recherche", 0.8, 10)
 */
export async function SEARCH_SIMILAR(
  queryText: string, 
  threshold: number = 0.7, 
  limit: number = 10
): Promise<any[]> {
  if (typeof queryText !== 'string') {
    throw new Error('SEARCH_SIMILAR: Le premier paramètre doit être une chaîne de caractères');
  }
  
  try {
    const results = await spatialVectorService.searchSimilar(queryText, threshold, limit);
    return results.map(result => ({
      table: result.tableName,
      row: result.rowId,
      column: result.columnName,
      content: result.content,
      similarity: Math.round(result.similarity * 10000) / 10000 // Arrondi à 4 décimales
    }));
  } catch (error) {
    log.error('SEARCH_SIMILAR error:', error);
    throw new Error(`SEARCH_SIMILAR: ${error.message}`);
  }
}

/**
 * Calcule la similarité entre deux textes
 * Utilisation: TEXT_SIMILARITY("Premier texte", "Deuxième texte")
 */
export async function TEXT_SIMILARITY(text1: string, text2: string): Promise<number> {
  if (typeof text1 !== 'string' || typeof text2 !== 'string') {
    throw new Error('TEXT_SIMILARITY: Les deux paramètres doivent être des chaînes de caractères');
  }
  
  try {
    const embedding1 = await spatialVectorService.generateEmbedding(text1);
    const embedding2 = await spatialVectorService.generateEmbedding(text2);
    
    // Calcul de la similarité cosinus
    const dotProduct = embedding1.reduce((sum, a, i) => sum + a * embedding2[i], 0);
    const norm1 = Math.sqrt(embedding1.reduce((sum, a) => sum + a * a, 0));
    const norm2 = Math.sqrt(embedding2.reduce((sum, a) => sum + a * a, 0));
    
    const similarity = dotProduct / (norm1 * norm2);
    return Math.round(similarity * 10000) / 10000; // Arrondi à 4 décimales
    
  } catch (error) {
    log.error('TEXT_SIMILARITY error:', error);
    throw new Error(`TEXT_SIMILARITY: ${error.message}`);
  }
}

// ============================================================================
// FONCTIONS SPATIALES NATIVES
// ============================================================================

/**
 * Crée un point géographique à partir de coordonnées
 * Utilisation: GEO_POINT(2.3522, 48.8566) // Notre-Dame de Paris
 */
export function GEO_POINT(longitude: number, latitude: number, srid: number = 4326): object {
  if (typeof longitude !== 'number' || typeof latitude !== 'number') {
    throw new Error('GEO_POINT: Les coordonnées doivent être des nombres');
  }
  
  if (longitude < -180 || longitude > 180) {
    throw new Error('GEO_POINT: La longitude doit être entre -180 et 180');
  }
  
  if (latitude < -90 || latitude > 90) {
    throw new Error('GEO_POINT: La latitude doit être entre -90 et 90');
  }
  
  return {
    type: 'Point',
    coordinates: [longitude, latitude],
    srid
  };
}

/**
 * Calcule la distance entre deux points géographiques (en mètres)
 * Utilisation: GEO_DISTANCE(GEO_POINT(2.3522, 48.8566), GEO_POINT(2.2945, 48.8582))
 */
export async function GEO_DISTANCE(point1: any, point2: any): Promise<number> {
  if (!point1 || !point2 || point1.type !== 'Point' || point2.type !== 'Point') {
    throw new Error('GEO_DISTANCE: Les deux paramètres doivent être des points géographiques');
  }
  
  const [lon1, lat1] = point1.coordinates;
  const [lon2, lat2] = point2.coordinates;
  
  // Formule de Haversine pour le calcul de distance
  const R = 6371000; // Rayon de la Terre en mètres
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distance = R * c;
  
  return Math.round(distance * 100) / 100; // Arrondi au centimètre
}

/**
 * Crée un polygone à partir d'une liste de points
 * Utilisation: GEO_POLYGON([[2.35, 48.85], [2.36, 48.85], [2.36, 48.86], [2.35, 48.86], [2.35, 48.85]])
 */
export function GEO_POLYGON(coordinates: number[][][], srid: number = 4326): object {
  if (!Array.isArray(coordinates) || coordinates.length === 0) {
    throw new Error('GEO_POLYGON: Les coordonnées doivent être un tableau de polygones');
  }
  
  // Validation du format des coordonnées
  for (const ring of coordinates) {
    if (!Array.isArray(ring) || ring.length < 4) {
      throw new Error('GEO_POLYGON: Chaque anneau doit avoir au moins 4 points');
    }
    
    // Vérifier que le polygone est fermé
    const first = ring[0];
    const last = ring[ring.length - 1];
    if (first[0] !== last[0] || first[1] !== last[1]) {
      throw new Error('GEO_POLYGON: Le polygone doit être fermé (premier point = dernier point)');
    }
  }
  
  return {
    type: 'Polygon',
    coordinates,
    srid
  };
}

/**
 * Calcule l'aire d'un polygone (en mètres carrés)
 * Utilisation: GEO_AREA(mon_polygone)
 */
export function GEO_AREA(polygon: any): number {
  if (!polygon || polygon.type !== 'Polygon') {
    throw new Error('GEO_AREA: Le paramètre doit être un polygone');
  }
  
  const coordinates = polygon.coordinates[0]; // Premier anneau (extérieur)
  let area = 0;
  
  // Algorithme de la formule de Shoelace adaptée pour les coordonnées géographiques
  const R = 6371000; // Rayon de la Terre
  
  for (let i = 0; i < coordinates.length - 1; i++) {
    const [lon1, lat1] = coordinates[i];
    const [lon2, lat2] = coordinates[i + 1];
    
    const lat1Rad = lat1 * Math.PI / 180;
    const lat2Rad = lat2 * Math.PI / 180;
    const deltaLon = (lon2 - lon1) * Math.PI / 180;
    
    area += deltaLon * (2 + Math.sin(lat1Rad) + Math.sin(lat2Rad));
  }
  
  area = Math.abs(area * R * R / 2);
  return Math.round(area * 100) / 100; // Arrondi au centimètre carré
}

/**
 * Vérifie si un point est à l'intérieur d'un polygone
 * Utilisation: GEO_CONTAINS(mon_polygone, GEO_POINT(2.35, 48.85))
 */
export function GEO_CONTAINS(polygon: any, point: any): boolean {
  if (!polygon || polygon.type !== 'Polygon') {
    throw new Error('GEO_CONTAINS: Le premier paramètre doit être un polygone');
  }
  
  if (!point || point.type !== 'Point') {
    throw new Error('GEO_CONTAINS: Le deuxième paramètre doit être un point');
  }
  
  const [x, y] = point.coordinates;
  const vertices = polygon.coordinates[0];
  
  // Algorithme du ray casting
  let inside = false;
  for (let i = 0, j = vertices.length - 1; i < vertices.length; j = i++) {
    const [xi, yi] = vertices[i];
    const [xj, yj] = vertices[j];
    
    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  
  return inside;
}

/**
 * Recherche de points dans un rayon donné
 * Utilisation: GEO_SEARCH_NEARBY(GEO_POINT(2.35, 48.85), 1000) // 1km
 */
export async function GEO_SEARCH_NEARBY(
  centerPoint: any, 
  radiusMeters: number, 
  limit: number = 10
): Promise<any[]> {
  if (!centerPoint || centerPoint.type !== 'Point') {
    throw new Error('GEO_SEARCH_NEARBY: Le premier paramètre doit être un point géographique');
  }
  
  if (typeof radiusMeters !== 'number' || radiusMeters <= 0) {
    throw new Error('GEO_SEARCH_NEARBY: Le rayon doit être un nombre positif');
  }
  
  try {
    return await spatialVectorService.searchNearby(centerPoint, radiusMeters, limit);
  } catch (error) {
    log.error('GEO_SEARCH_NEARBY error:', error);
    throw new Error(`GEO_SEARCH_NEARBY: ${error.message}`);
  }
}

// ============================================================================
// FONCTIONS HYBRIDES SPATIAL + VECTORIEL
// ============================================================================

/**
 * Recherche hybride : proximité géographique + similarité textuelle
 * Utilisation: HYBRID_SEARCH("restaurant italien", GEO_POINT(2.35, 48.85), 500, 0.7)
 */
export async function HYBRID_SEARCH(
  queryText: string,
  centerPoint: any,
  radiusMeters: number,
  textSimilarityThreshold: number = 0.7,
  limit: number = 10
): Promise<any[]> {
  if (typeof queryText !== 'string') {
    throw new Error('HYBRID_SEARCH: Le texte de recherche doit être une chaîne');
  }
  
  if (!centerPoint || centerPoint.type !== 'Point') {
    throw new Error('HYBRID_SEARCH: Le point central doit être un point géographique');
  }
  
  try {
    // Recherche spatiale
    const spatialResults = await spatialVectorService.searchNearby(centerPoint, radiusMeters, limit * 2);
    
    // Pour chaque résultat spatial, calculer la similarité textuelle
    const hybridResults = [];
    
    for (const spatialResult of spatialResults) {
      // Ici on devrait récupérer le contenu textuel associé à chaque résultat spatial
      // Pour la démo, on simule une similarité
      const similarity = Math.random() * 0.5 + 0.5; // Simulation
      
      if (similarity >= textSimilarityThreshold) {
        hybridResults.push({
          ...spatialResult,
          textSimilarity: Math.round(similarity * 10000) / 10000,
          hybridScore: (similarity + (1 - spatialResult.distance / radiusMeters)) / 2
        });
      }
    }
    
    // Tri par score hybride
    hybridResults.sort((a, b) => b.hybridScore - a.hybridScore);
    return hybridResults.slice(0, limit);
    
  } catch (error) {
    log.error('HYBRID_SEARCH error:', error);
    throw new Error(`HYBRID_SEARCH: ${error.message}`);
  }
}

// ============================================================================
// FONCTIONS UTILITAIRES
// ============================================================================

/**
 * Obtient les statistiques du service spatial/vectoriel
 * Utilisation: SPATIAL_STATS()
 */
export async function SPATIAL_STATS(): Promise<object> {
  try {
    const stats = await spatialVectorService.getStats();
    return {
      embeddings_count: stats.embeddings,
      geometries_count: stats.geometries,
      status: 'operational',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    log.error('SPATIAL_STATS error:', error);
    return {
      embeddings_count: 0,
      geometries_count: 0,
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Conversion de coordonnées (par exemple, de degrés décimaux vers DMS)
 * Utilisation: GEO_CONVERT_COORDS(2.3522, "DD_TO_DMS")
 */
export function GEO_CONVERT_COORDS(coordinate: number, format: string): string {
  if (typeof coordinate !== 'number') {
    throw new Error('GEO_CONVERT_COORDS: La coordonnée doit être un nombre');
  }
  
  switch (format.toUpperCase()) {
    case 'DD_TO_DMS': // Degrés décimaux vers degrés, minutes, secondes
      const degrees = Math.floor(Math.abs(coordinate));
      const minutes = Math.floor((Math.abs(coordinate) - degrees) * 60);
      const seconds = ((Math.abs(coordinate) - degrees) * 60 - minutes) * 60;
      const direction = coordinate >= 0 ? '' : '-';
      return `${direction}${degrees}°${minutes}'${seconds.toFixed(2)}"`;
      
    case 'NORMALIZE_LON': // Normalise longitude entre -180 et 180
      while (coordinate > 180) coordinate -= 360;
      while (coordinate < -180) coordinate += 360;
      return coordinate.toString();
      
    case 'NORMALIZE_LAT': // Normalise latitude entre -90 et 90
      return Math.max(-90, Math.min(90, coordinate)).toString();
      
    default:
      throw new Error(`GEO_CONVERT_COORDS: Format non supporté: ${format}`);
  }
}