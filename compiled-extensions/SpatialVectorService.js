// Service spatial et vectoriel pour Grist - Version JavaScript
const axios = require('axios');

class SpatialVectorService {
  constructor() {
    this.albertApiUrl = process.env.ALBERT_API_URL || 'https://albert.api.etalab.gouv.fr/v1';
    this.albertApiToken = process.env.ALBERT_API_TOKEN;
    this.simulationMode = !this.albertApiToken;
  }

  // Générer un embedding via l'API Albert
  async generateEmbedding(text) {
    if (this.simulationMode) {
      // Mode simulation - génère un embedding aléatoire de 1024 dimensions
      return Array.from({ length: 1024 }, () => Math.random() * 2 - 1);
    }

    try {
      const response = await axios.post(`${this.albertApiUrl}/embeddings`, {
        model: 'intfloat/multilingual-e5-large',
        input: text
      }, {
        headers: {
          'Authorization': `Bearer ${this.albertApiToken}`,
          'Content-Type': 'application/json'
        }
      });

      return response.data.data[0].embedding;
    } catch (error) {
      console.error('Erreur génération embedding Albert:', error.message);
      // Fallback vers simulation
      return Array.from({ length: 1024 }, () => Math.random() * 2 - 1);
    }
  }

  // Calculer similarité cosinus entre deux vecteurs
  calculateCosineSimilarity(vectorA, vectorB) {
    if (vectorA.length !== vectorB.length) {
      throw new Error('Les vecteurs doivent avoir la même dimension');
    }

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < vectorA.length; i++) {
      dotProduct += vectorA[i] * vectorB[i];
      normA += vectorA[i] * vectorA[i];
      normB += vectorB[i] * vectorB[i];
    }

    if (normA === 0 || normB === 0) return 0;
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  // Rechercher les éléments les plus similaires
  searchSimilar(queryVector, dataVectors, limit = 5) {
    const similarities = dataVectors.map((vector, index) => ({
      index,
      similarity: this.calculateCosineSimilarity(queryVector, vector.embedding || vector),
      data: vector
    }));

    return similarities
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);
  }

  // Calculer distance géographique (formule haversine)
  calculateGeoDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Rayon de la Terre en mètres
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // Distance en mètres
  }

  // Parser WKT (Well-Known Text)
  parseWKT(wkt) {
    const pointMatch = wkt.match(/POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/i);
    if (pointMatch) {
      return {
        type: 'Point',
        coordinates: [parseFloat(pointMatch[1]), parseFloat(pointMatch[2])]
      };
    }
    
    throw new Error('Format WKT non supporté: ' + wkt);
  }

  // Calculer aire d'une géométrie (approximation simple)
  calculateGeoArea(geometry) {
    if (geometry.type === 'Point') {
      return 0;
    }
    // Implémentation simplifiée - à étendre pour polygones
    return 0;
  }

  // Vérifier si un point est contenu dans une géométrie
  checkGeoContains(geometry1, geometry2) {
    // Implémentation simplifiée
    if (geometry1.type === 'Point' && geometry2.type === 'Point') {
      return geometry1.coordinates[0] === geometry2.coordinates[0] && 
             geometry1.coordinates[1] === geometry2.coordinates[1];
    }
    return false;
  }
}

module.exports = { SpatialVectorService };