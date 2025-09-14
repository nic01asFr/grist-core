// Fonctions spatiales et vectorielles natives pour Grist - Version JavaScript
const { SpatialVectorService } = require('./SpatialVectorService');

// Instance globale du service
const spatialService = new SpatialVectorService();

// Fonctions géographiques
function GEO_DISTANCE(point1, point2) {
  try {
    const geom1 = spatialService.parseWKT(point1.toString());
    const geom2 = spatialService.parseWKT(point2.toString());
    
    if (geom1.type === 'Point' && geom2.type === 'Point') {
      return spatialService.calculateGeoDistance(
        geom1.coordinates[1], geom1.coordinates[0],
        geom2.coordinates[1], geom2.coordinates[0]
      );
    }
    return null;
  } catch (error) {
    console.error('Erreur GEO_DISTANCE:', error.message);
    return null;
  }
}

function GEO_AREA(geometry) {
  try {
    const geom = spatialService.parseWKT(geometry.toString());
    return spatialService.calculateGeoArea(geom);
  } catch (error) {
    console.error('Erreur GEO_AREA:', error.message);
    return null;
  }
}

function GEO_CONTAINS(geometry1, geometry2) {
  try {
    const geom1 = spatialService.parseWKT(geometry1.toString());
    const geom2 = spatialService.parseWKT(geometry2.toString());
    return spatialService.checkGeoContains(geom1, geom2);
  } catch (error) {
    console.error('Erreur GEO_CONTAINS:', error.message);
    return false;
  }
}

function GEO_BUFFER(geometry, distance) {
  // Implémentation simplifiée du buffer
  try {
    const geom = spatialService.parseWKT(geometry.toString());
    if (geom.type === 'Point') {
      // Retourne un cercle approximatif autour du point
      const [x, y] = geom.coordinates;
      const radius = distance / 111320; // Approximation degrés
      return `POLYGON((${x-radius} ${y-radius},${x+radius} ${y-radius},${x+radius} ${y+radius},${x-radius} ${y+radius},${x-radius} ${y-radius}))`;
    }
    return geometry.toString();
  } catch (error) {
    console.error('Erreur GEO_BUFFER:', error.message);
    return geometry.toString();
  }
}

// Fonctions vectorielles
async function GENERATE_EMBEDDING(text) {
  try {
    const embedding = await spatialService.generateEmbedding(text.toString());
    return JSON.stringify(embedding);
  } catch (error) {
    console.error('Erreur GENERATE_EMBEDDING:', error.message);
    return null;
  }
}

function SEARCH_SIMILAR(queryVector, dataArray, limit = 5) {
  try {
    const query = JSON.parse(queryVector.toString());
    const data = Array.isArray(dataArray) ? dataArray : [dataArray];
    
    const vectors = data.map((item, index) => ({
      index,
      embedding: typeof item === 'string' ? JSON.parse(item) : item,
      originalData: item
    }));
    
    const results = spatialService.searchSimilar(query, vectors, limit);
    return JSON.stringify(results.map(r => ({
      similarity: r.similarity,
      data: r.data.originalData
    })));
  } catch (error) {
    console.error('Erreur SEARCH_SIMILAR:', error.message);
    return JSON.stringify([]);
  }
}

function VECTOR_SIMILARITY(vector1, vector2) {
  try {
    const v1 = JSON.parse(vector1.toString());
    const v2 = JSON.parse(vector2.toString());
    return spatialService.calculateCosineSimilarity(v1, v2);
  } catch (error) {
    console.error('Erreur VECTOR_SIMILARITY:', error.message);
    return 0;
  }
}

async function HYBRID_SEARCH(query, dataArray, geoPoint = null, radius = null) {
  try {
    // Combinaison recherche vectorielle + spatiale
    const embedding = await spatialService.generateEmbedding(query.toString());
    let results = SEARCH_SIMILAR(JSON.stringify(embedding), dataArray);
    
    if (geoPoint && radius) {
      // Filtrage spatial additionnel (implémentation simplifiée)
      const spatialResults = JSON.parse(results).filter(item => {
        // Logique de filtrage spatial à implémenter
        return true;
      });
      return JSON.stringify(spatialResults);
    }
    
    return results;
  } catch (error) {
    console.error('Erreur HYBRID_SEARCH:', error.message);
    return JSON.stringify([]);
  }
}

// Export des fonctions pour Grist
const nativeSpatialFunctions = {
  GEO_DISTANCE,
  GEO_AREA,
  GEO_CONTAINS,
  GEO_BUFFER,
  GENERATE_EMBEDDING,
  SEARCH_SIMILAR,
  VECTOR_SIMILARITY,
  HYBRID_SEARCH
};

module.exports = nativeSpatialFunctions;