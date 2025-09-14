/**
 * Types et définitions pour les colonnes spatiales et vectorielles dans Grist
 * Intégration native des types géospatiaux et embeddings vectoriels
 */

// CellValue type import - utilisé pour l'interface SpatialCellValue

// ============================================================================
// TYPES DE DONNÉES SPATIALES
// ============================================================================

export interface GeoPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
  srid?: number; // Système de référence spatiale (défaut: 4326 WGS84)
}

export interface GeoPolygon {
  type: 'Polygon';
  coordinates: number[][][]; // Array de rings, chaque ring est un array de [lon, lat]
  srid?: number;
}

export interface GeoLineString {
  type: 'LineString';
  coordinates: number[][]; // Array de points [lon, lat]
  srid?: number;
}

export interface GeoMultiPoint {
  type: 'MultiPoint';
  coordinates: number[][];
  srid?: number;
}

export interface GeoMultiPolygon {
  type: 'MultiPolygon';
  coordinates: number[][][][];
  srid?: number;
}

export interface GeoMultiLineString {
  type: 'MultiLineString';
  coordinates: number[][][];
  srid?: number;
}

// Union de tous les types géométriques
export type Geometry = 
  | GeoPoint 
  | GeoPolygon 
  | GeoLineString 
  | GeoMultiPoint 
  | GeoMultiPolygon 
  | GeoMultiLineString;

// ============================================================================
// TYPES DE DONNÉES VECTORIELLES
// ============================================================================

export interface VectorEmbedding {
  type: 'Vector';
  dimensions: number;
  values: number[];
  model?: string; // Modèle utilisé pour générer l'embedding
  source?: string; // Texte source de l'embedding
  timestamp?: number; // Timestamp de génération
}

export interface SimilarityResult {
  score: number; // Score de similarité (0-1)
  source: {
    table: string;
    row: number;
    column: string;
  };
  content?: string;
}

// ============================================================================
// DÉFINITIONS DES COLONNES GRIST ÉTENDUES
// ============================================================================

// Extension des types de colonnes Grist existants
export enum SpatialColumnTypes {
  GeoPoint = 'GeoPoint',
  GeoPolygon = 'GeoPolygon', 
  GeoLineString = 'GeoLineString',
  GeoMultiPoint = 'GeoMultiPoint',
  GeoMultiPolygon = 'GeoMultiPolygon',
  GeoMultiLineString = 'GeoMultiLineString',
  Vector = 'Vector'
}

// Options pour les colonnes spatiales
export interface SpatialColumnOptions {
  // Options communes
  srid?: number; // Système de référence spatiale (défaut: 4326)
  precision?: number; // Précision décimale pour les coordonnées
  
  // Options spécifiques aux vecteurs
  dimensions?: number; // Nombre de dimensions pour les vecteurs
  model?: string; // Modèle d'embedding par défaut
  autoGenerate?: boolean; // Génération automatique d'embeddings
  sourceColumn?: string; // Colonne source pour génération automatique
  
  // Options d'affichage
  displayFormat?: 'coordinates' | 'dms' | 'address'; // Format d'affichage
  mapProvider?: 'openstreetmap' | 'google' | 'mapbox'; // Fournisseur de cartes
  showMap?: boolean; // Afficher une carte dans la cellule
  
  // Options de validation
  boundsCheck?: {
    minLat?: number;
    maxLat?: number;
    minLon?: number;
    maxLon?: number;
  };
}

// ============================================================================
// FONCTIONS D'AIDE POUR LA VALIDATION
// ============================================================================

export function isValidGeoPoint(value: any): value is GeoPoint {
  return value && 
         value.type === 'Point' && 
         Array.isArray(value.coordinates) &&
         value.coordinates.length === 2 &&
         typeof value.coordinates[0] === 'number' &&
         typeof value.coordinates[1] === 'number' &&
         value.coordinates[0] >= -180 && value.coordinates[0] <= 180 &&
         value.coordinates[1] >= -90 && value.coordinates[1] <= 90;
}

export function isValidGeoPolygon(value: any): value is GeoPolygon {
  if (!value || value.type !== 'Polygon' || !Array.isArray(value.coordinates)) {
    return false;
  }
  
  for (const ring of value.coordinates) {
    if (!Array.isArray(ring) || ring.length < 4) return false;
    
    // Vérifier que le ring est fermé
    const first = ring[0];
    const last = ring[ring.length - 1];
    if (!Array.isArray(first) || !Array.isArray(last) ||
        first.length !== 2 || last.length !== 2 ||
        first[0] !== last[0] || first[1] !== last[1]) {
      return false;
    }
    
    // Vérifier chaque point
    for (const point of ring) {
      if (!Array.isArray(point) || point.length !== 2 ||
          typeof point[0] !== 'number' || typeof point[1] !== 'number' ||
          point[0] < -180 || point[0] > 180 ||
          point[1] < -90 || point[1] > 90) {
        return false;
      }
    }
  }
  
  return true;
}

export function isValidVectorEmbedding(value: any): value is VectorEmbedding {
  return value &&
         value.type === 'Vector' &&
         typeof value.dimensions === 'number' &&
         Array.isArray(value.values) &&
         value.values.length === value.dimensions &&
         value.values.every((v: any) => typeof v === 'number' && !isNaN(v));
}

// ============================================================================
// FONCTIONS DE CONVERSION ET FORMATAGE
// ============================================================================

export function formatGeoPoint(point: GeoPoint, format: 'coordinates' | 'dms' = 'coordinates'): string {
  const [lon, lat] = point.coordinates;
  
  switch (format) {
    case 'coordinates':
      return `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
      
    case 'dms':
      const latDMS = toDMS(lat, 'lat');
      const lonDMS = toDMS(lon, 'lon');
      return `${latDMS}, ${lonDMS}`;
      
    default:
      return `${lat}, ${lon}`;
  }
}

function toDMS(coordinate: number, type: 'lat' | 'lon'): string {
  const degrees = Math.floor(Math.abs(coordinate));
  const minutes = Math.floor((Math.abs(coordinate) - degrees) * 60);
  const seconds = ((Math.abs(coordinate) - degrees) * 60 - minutes) * 60;
  
  let direction: string;
  if (type === 'lat') {
    direction = coordinate >= 0 ? 'N' : 'S';
  } else {
    direction = coordinate >= 0 ? 'E' : 'W';
  }
  
  return `${degrees}°${minutes}'${seconds.toFixed(1)}"${direction}`;
}

export function formatVectorEmbedding(vector: VectorEmbedding): string {
  const preview = vector.values.slice(0, 3).map(v => v.toFixed(3)).join(', ');
  return `Vector(${vector.dimensions}D): [${preview}...]`;
}

// ============================================================================
// PARSEURS POUR L'IMPORTATION DE DONNÉES
// ============================================================================

export function parseGeoPoint(input: string): GeoPoint | null {
  try {
    // Format: "lat, lon" ou "latitude, longitude"
    const coords = input.split(',').map(s => parseFloat(s.trim()));
    if (coords.length === 2 && !isNaN(coords[0]) && !isNaN(coords[1])) {
      const [lat, lon] = coords;
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        return {
          type: 'Point',
          coordinates: [lon, lat], // GeoJSON utilise [lon, lat]
          srid: 4326
        };
      }
    }
    
    // Format WKT: "POINT(lon lat)"
    const wktMatch = input.match(/POINT\s*\(\s*([+-]?\d+\.?\d*)\s+([+-]?\d+\.?\d*)\s*\)/i);
    if (wktMatch) {
      const lon = parseFloat(wktMatch[1]);
      const lat = parseFloat(wktMatch[2]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        return {
          type: 'Point',
          coordinates: [lon, lat],
          srid: 4326
        };
      }
    }
    
    return null;
  } catch {
    return null;
  }
}

export function parseVectorEmbedding(input: string): VectorEmbedding | null {
  try {
    // Format JSON: "[1.0, 2.0, 3.0, ...]"
    const values = JSON.parse(input);
    if (Array.isArray(values) && values.every(v => typeof v === 'number' && !isNaN(v))) {
      return {
        type: 'Vector',
        dimensions: values.length,
        values: values,
        timestamp: Date.now()
      };
    }
    
    return null;
  } catch {
    return null;
  }
}

// ============================================================================
// GÉNÉRATEURS DE VALEURS PAR DÉFAUT
// ============================================================================

export function createDefaultGeoPoint(lat: number = 48.8566, lon: number = 2.3522): GeoPoint {
  return {
    type: 'Point',
    coordinates: [lon, lat], // Paris par défaut
    srid: 4326
  };
}

export function createEmptyVector(dimensions: number = 1024): VectorEmbedding {
  return {
    type: 'Vector',
    dimensions: dimensions,
    values: new Array(dimensions).fill(0),
    timestamp: Date.now()
  };
}

// ============================================================================
// TYPES POUR L'INTÉGRATION AVEC L'API GRIST
// ============================================================================

export interface SpatialCellValue {
  spatial?: Geometry;
  vector?: VectorEmbedding;
}

export interface SpatialActionBundle {
  stored: Geometry[];
  undo: Geometry[];
}

// Options pour les opérations spatiales en lot
export interface BatchSpatialOperation {
  operation: 'distance' | 'area' | 'contains' | 'similarity';
  source: {
    table: string;
    column: string;
    rows?: number[];
  };
  target?: {
    table: string;
    column: string;
    rows?: number[];
  };
  parameters?: {
    threshold?: number;
    radius?: number;
    limit?: number;
  };
}