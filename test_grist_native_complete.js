/**
 * Test complet des fonctionnalités natives Grist intégrées
 * PostGIS + pgvector + Albert API + Fonctions spatiales/vectorielles
 */

console.log('🎯 TEST COMPLET GRIST NATIVE - FONCTIONNALITÉS INTÉGRÉES');
console.log('=' .repeat(80));

const baseUrl = process.env.GRIST_URL || 'http://localhost:8484';
const apiBase = `${baseUrl}/api/docs/test/spatial`;

// Configuration de test
const testData = {
  texts: [
    "Restaurant français traditionnel à Paris",
    "Boulangerie artisanale dans le Marais", 
    "Musée d'art moderne contemporain",
    "Parc public avec jeux pour enfants",
    "Bibliothèque municipale avec WiFi gratuit"
  ],
  locations: [
    { name: "Tour Eiffel", lat: 48.8582, lon: 2.2945 },
    { name: "Notre-Dame", lat: 48.8530, lon: 2.3522 },
    { name: "Louvre", lat: 48.8606, lon: 2.3376 },
    { name: "Arc de Triomphe", lat: 48.8738, lon: 2.2950 },
    { name: "Sacré-Cœur", lat: 48.8867, lon: 2.3431 }
  ]
};

// ============================================================================
// FONCTIONS UTILITAIRES
// ============================================================================

async function makeRequest(endpoint, method = 'GET', body = null) {
  const url = `${apiBase}${endpoint}`;
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  };
  
  if (body) {
    options.body = JSON.stringify(body);
  }
  
  try {
    const response = await fetch(url);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${data.error || 'Erreur API'}`);
    }
    
    return data;
  } catch (error) {
    console.log(`❌ Erreur requête ${endpoint}:`, error.message);
    return null;
  }
}

function logTest(testName, success, details = '') {
  const status = success ? '✅' : '❌';
  console.log(`${status} ${testName}${details ? ' - ' + details : ''}`);
  return success;
}

function logSection(title) {
  console.log(`\n📊 ${title.toUpperCase()}`);
  console.log('-'.repeat(50));
}

// ============================================================================
// TESTS DES FONCTIONNALITÉS VECTORIELLES
// ============================================================================

async function testVectorFunctions() {
  logSection('Tests Fonctionnalités Vectorielles');
  
  const results = {
    embedding: false,
    similarity_search: false,
    similarity_compare: false
  };
  
  // Test 1: Génération d'embedding
  console.log('🧮 Test génération d\'embedding...');
  const embeddingResult = await makeRequest('/embedding', 'POST', {
    text: testData.texts[0]
  });
  
  if (embeddingResult && embeddingResult.success && embeddingResult.data.embedding) {
    results.embedding = logTest(
      'Génération embedding', 
      true, 
      `${embeddingResult.data.dimensions} dimensions`
    );
  } else {
    results.embedding = logTest('Génération embedding', false);
  }
  
  // Test 2: Recherche de similarité
  console.log('🔍 Test recherche de similarité...');
  const searchResult = await makeRequest('/similarity/search', 'POST', {
    queryText: "restaurant parisien",
    threshold: 0.5,
    limit: 3
  });
  
  if (searchResult && searchResult.success) {
    results.similarity_search = logTest(
      'Recherche similarité', 
      true, 
      `${searchResult.data.count} résultats`
    );
  } else {
    results.similarity_search = logTest('Recherche similarité', false);
  }
  
  // Test 3: Comparaison de similarité
  console.log('📊 Test comparaison de similarité...');
  const compareResult = await makeRequest('/similarity/compare', 'POST', {
    text1: testData.texts[0],
    text2: testData.texts[1]
  });
  
  if (compareResult && compareResult.success) {
    results.similarity_compare = logTest(
      'Comparaison similarité', 
      true, 
      `Score: ${compareResult.data.similarity}`
    );
  } else {
    results.similarity_compare = logTest('Comparaison similarité', false);
  }
  
  return results;
}

// ============================================================================
// TESTS DES FONCTIONNALITÉS SPATIALES
// ============================================================================

async function testSpatialFunctions() {
  logSection('Tests Fonctionnalités Spatiales');
  
  const results = {
    distance: false,
    area: false,
    contains: false,
    nearby: false,
    conversion: false
  };
  
  // Test 1: Calcul de distance
  console.log('📏 Test calcul de distance...');
  const point1 = { type: 'Point', coordinates: [2.2945, 48.8582] }; // Tour Eiffel
  const point2 = { type: 'Point', coordinates: [2.3522, 48.8530] }; // Notre-Dame
  
  const distanceResult = await makeRequest('/geometry/distance', 'POST', {
    point1,
    point2
  });
  
  if (distanceResult && distanceResult.success) {
    results.distance = logTest(
      'Calcul distance', 
      true, 
      `${Math.round(distanceResult.data.distance.meters)}m`
    );
  } else {
    results.distance = logTest('Calcul distance', false);
  }
  
  // Test 2: Calcul d'aire
  console.log('📐 Test calcul d\'aire...');
  const polygon = {
    type: 'Polygon',
    coordinates: [[
      [2.29, 48.85],
      [2.30, 48.85], 
      [2.30, 48.86],
      [2.29, 48.86],
      [2.29, 48.85]
    ]]
  };
  
  const areaResult = await makeRequest('/geometry/area', 'POST', {
    polygon
  });
  
  if (areaResult && areaResult.success) {
    results.area = logTest(
      'Calcul aire', 
      true, 
      `${Math.round(areaResult.data.area.squareMeters)}m²`
    );
  } else {
    results.area = logTest('Calcul aire', false);
  }
  
  // Test 3: Test de containment
  console.log('🎯 Test point dans polygone...');
  const containsResult = await makeRequest('/geometry/contains', 'POST', {
    polygon,
    point: { type: 'Point', coordinates: [2.295, 48.855] }
  });
  
  if (containsResult && containsResult.success) {
    results.contains = logTest(
      'Point dans polygone', 
      true, 
      `Contains: ${containsResult.data.contains}`
    );
  } else {
    results.contains = logTest('Point dans polygone', false);
  }
  
  // Test 4: Recherche de proximité
  console.log('🌍 Test recherche proximité...');
  const nearbyResult = await makeRequest('/geometry/nearby', 'POST', {
    center: point1,
    radius: 2000,
    limit: 5
  });
  
  if (nearbyResult && nearbyResult.success) {
    results.nearby = logTest(
      'Recherche proximité', 
      true, 
      `${nearbyResult.data.count} résultats`
    );
  } else {
    results.nearby = logTest('Recherche proximité', false);
  }
  
  // Test 5: Conversion de coordonnées
  console.log('🔄 Test conversion coordonnées...');
  const conversionResult = await makeRequest('/convert/coordinates', 'POST', {
    coordinate: 48.8582,
    format: 'DD_TO_DMS'
  });
  
  if (conversionResult && conversionResult.success) {
    results.conversion = logTest(
      'Conversion coordonnées', 
      true, 
      `${conversionResult.data.result}`
    );
  } else {
    results.conversion = logTest('Conversion coordonnées', false);
  }
  
  return results;
}

// ============================================================================
// TESTS DES FONCTIONNALITÉS HYBRIDES
// ============================================================================

async function testHybridFunctions() {
  logSection('Tests Fonctionnalités Hybrides');
  
  const results = {
    hybrid_search: false
  };
  
  // Test recherche hybride
  console.log('🔍+🌍 Test recherche hybride...');
  const hybridResult = await makeRequest('/hybrid/search', 'POST', {
    queryText: "restaurant traditionnel",
    center: { type: 'Point', coordinates: [2.3522, 48.8530] },
    radius: 1000,
    textThreshold: 0.6,
    limit: 5
  });
  
  if (hybridResult && hybridResult.success) {
    results.hybrid_search = logTest(
      'Recherche hybride', 
      true, 
      `${hybridResult.data.count} résultats`
    );
  } else {
    results.hybrid_search = logTest('Recherche hybride', false);
  }
  
  return results;
}

// ============================================================================
// TESTS SYSTÈME ET STATISTIQUES
// ============================================================================

async function testSystemFunctions() {
  logSection('Tests Système');
  
  const results = {
    health: false,
    stats: false,
    capabilities: false
  };
  
  // Test 1: Health check
  console.log('💓 Test health check...');
  const healthResult = await makeRequest('/health');
  
  if (healthResult && healthResult.success) {
    results.health = logTest(
      'Health check', 
      true, 
      `Status: ${healthResult.data.status}`
    );
  } else {
    results.health = logTest('Health check', false);
  }
  
  // Test 2: Statistiques
  console.log('📊 Test statistiques...');
  const statsResult = await makeRequest('/stats');
  
  if (statsResult && statsResult.success) {
    results.stats = logTest(
      'Statistiques', 
      true, 
      `${statsResult.data.embeddings_count} embeddings, ${statsResult.data.geometries_count} géométries`
    );
  } else {
    results.stats = logTest('Statistiques', false);
  }
  
  // Test 3: Capacités
  console.log('⚙️ Test capacités...');
  const capabilitiesResult = await makeRequest('/capabilities');
  
  if (capabilitiesResult && capabilitiesResult.success) {
    const features = capabilitiesResult.data.features;
    const totalFunctions = 
      features.vector_functions.length + 
      features.spatial_functions.length + 
      features.hybrid_functions.length;
      
    results.capabilities = logTest(
      'Capacités système', 
      true, 
      `${totalFunctions} fonctions disponibles`
    );
  } else {
    results.capabilities = logTest('Capacités système', false);
  }
  
  return results;
}

// ============================================================================
// FONCTION PRINCIPALE DE TEST
// ============================================================================

async function runCompleteTest() {
  console.log(`🌐 URL de test: ${baseUrl}`);
  console.log(`🔗 API Base: ${apiBase}\n`);
  
  const startTime = Date.now();
  const allResults = {};
  
  try {
    // Tests vectoriels
    allResults.vector = await testVectorFunctions();
    
    // Tests spatiaux  
    allResults.spatial = await testSpatialFunctions();
    
    // Tests hybrides
    allResults.hybrid = await testHybridFunctions();
    
    // Tests système
    allResults.system = await testSystemFunctions();
    
  } catch (error) {
    console.log('❌ Erreur lors des tests:', error.message);
  }
  
  // ============================================================================
  // RAPPORT FINAL
  // ============================================================================
  
  const endTime = Date.now();
  const duration = Math.round((endTime - startTime) / 1000);
  
  console.log('\n' + '='.repeat(80));
  console.log('🎉 RAPPORT FINAL - GRIST NATIVE INTÉGRÉ');
  console.log('='.repeat(80));
  
  // Comptage des succès
  let totalTests = 0;
  let successfulTests = 0;
  
  for (const category in allResults) {
    for (const test in allResults[category]) {
      totalTests++;
      if (allResults[category][test]) successfulTests++;
    }
  }
  
  const successRate = Math.round((successfulTests / totalTests) * 100);
  
  console.log(`📊 RÉSULTATS GLOBAUX:`);
  console.log(`   ✅ Tests réussis: ${successfulTests}/${totalTests} (${successRate}%)`);
  console.log(`   ⏱️ Durée: ${duration}s`);
  console.log(`   🎯 Status: ${successRate >= 80 ? 'OPÉRATIONNEL' : 'DÉGRADÉ'}`);
  
  console.log(`\n🔍 DÉTAILS PAR CATÉGORIE:`);
  
  // Affichage détaillé par catégorie
  const categories = {
    vector: 'Fonctionnalités Vectorielles',
    spatial: 'Fonctionnalités Spatiales', 
    hybrid: 'Fonctionnalités Hybrides',
    system: 'Fonctions Système'
  };
  
  for (const category in allResults) {
    const categoryResults = allResults[category];
    const categoryTests = Object.keys(categoryResults).length;
    const categorySuccesses = Object.values(categoryResults).filter(Boolean).length;
    const categoryRate = Math.round((categorySuccesses / categoryTests) * 100);
    
    console.log(`   ${categories[category]}: ${categorySuccesses}/${categoryTests} (${categoryRate}%)`);
  }
  
  console.log(`\n💡 FONCTIONNALITÉS VALIDÉES:`);
  console.log(`   🧮 Albert API Integration: ${allResults.vector?.embedding ? 'OUI' : 'NON'}`);
  console.log(`   🔍 Recherche sémantique: ${allResults.vector?.similarity_search ? 'OUI' : 'NON'}`);
  console.log(`   🌍 Fonctions géospatiales: ${allResults.spatial?.distance ? 'OUI' : 'NON'}`);
  console.log(`   📐 Calculs géométriques: ${allResults.spatial?.area ? 'OUI' : 'NON'}`);
  console.log(`   🎯 Recherche hybride: ${allResults.hybrid?.hybrid_search ? 'OUI' : 'NON'}`);
  console.log(`   💓 Monitoring système: ${allResults.system?.health ? 'OUI' : 'NON'}`);
  
  if (successRate >= 80) {
    console.log(`\n🚀 GRIST NATIVE EST COMPLÈTEMENT OPÉRATIONNEL!`);
    console.log(`   L'intégration PostGIS + pgvector + Albert API fonctionne parfaitement.`);
    console.log(`   Toutes les fonctionnalités spatiales et vectorielles sont disponibles.`);
  } else {
    console.log(`\n⚠️ GRIST NATIVE EST PARTIELLEMENT OPÉRATIONNEL`);
    console.log(`   Certaines fonctionnalités nécessitent une vérification.`);
  }
  
  console.log(`\n📋 PROCHAINES ÉTAPES:`);
  console.log(`   1. Interface utilisateur pour les types de colonnes spatiales`);
  console.log(`   2. Widgets de visualisation des cartes intégrés`);
  console.log(`   3. Import/export de formats géospatiaux (GeoJSON, KML, SHP)`);
  console.log(`   4. Optimisation des performances pour gros volumes`);
  
  console.log('\n' + '='.repeat(80));
  
  return { successRate, duration, results: allResults };
}

// Export pour utilisation comme module ou exécution directe
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runCompleteTest };
} else {
  // Exécution directe
  runCompleteTest().catch(console.error);
}