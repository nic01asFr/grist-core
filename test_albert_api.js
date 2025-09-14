/**
 * Test direct de l'API Albert pour validation
 * Exécuter avec: node test_albert_api.js
 */

// Using built-in fetch available in Node.js 18+

// Configuration de test Albert API
const ALBERT_CONFIG = {
  apiUrl: process.env.ALBERT_API_URL || 'https://albert.api.etalab.gouv.fr/v1',
  apiToken: process.env.ALBERT_API_TOKEN || 'test-token',
  embeddingModel: process.env.ALBERT_MODEL_EMBEDDING || 'embeddings-small',
  dimensions: parseInt(process.env.EMBEDDING_DIMENSION || '1024')
};

console.log('🧪 Test API Albert - Configuration:');
console.log(JSON.stringify(ALBERT_CONFIG, null, 2));

async function testAlbertEmbedding(text) {
  console.log(`\n🚀 Test embedding pour: "${text}"`);
  
  if (!ALBERT_CONFIG.apiToken || ALBERT_CONFIG.apiToken === 'test-token') {
    console.log('⚠️  Token Albert non configuré, simulation de la réponse...');
    
    // Simulation de réponse Albert API
    const mockEmbedding = Array.from({length: ALBERT_CONFIG.dimensions}, (_, i) => 
      Math.sin(i * 0.01 + text.length * 0.1) * 0.1
    );
    
    return {
      success: true,
      data: {
        object: "list",
        data: [{
          object: "embedding", 
          embedding: mockEmbedding,
          index: 0
        }],
        model: ALBERT_CONFIG.embeddingModel,
        usage: {
          prompt_tokens: text.split(' ').length,
          total_tokens: text.split(' ').length
        }
      }
    };
  }

  try {
    const response = await fetch(`${ALBERT_CONFIG.apiUrl}/embeddings`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ALBERT_CONFIG.apiToken}`,
        'Content-Type': 'application/json',
        'User-Agent': 'Grist-Albert-Integration/1.0'
      },
      body: JSON.stringify({
        input: text,
        model: ALBERT_CONFIG.embeddingModel
      }),
      timeout: 10000
    });

    if (!response.ok) {
      throw new Error(`Albert API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return { success: true, data };

  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      fallback: 'Utilisation embedding local simulé'
    };
  }
}

async function testSimilarity(embeddings) {
  console.log('\n📊 Test calculs de similarité:');
  
  if (embeddings.length < 2) {
    console.log('⚠️  Pas assez d\'embeddings pour le test similarité');
    return;
  }

  const [emb1, emb2] = embeddings;
  
  // Similarité cosinus
  const dotProduct = emb1.reduce((sum, a, i) => sum + a * emb2[i], 0);
  const norm1 = Math.sqrt(emb1.reduce((sum, a) => sum + a * a, 0));
  const norm2 = Math.sqrt(emb2.reduce((sum, a) => sum + a * a, 0));
  const cosineSimilarity = dotProduct / (norm1 * norm2);
  
  // Distance euclidienne
  const euclideanDistance = Math.sqrt(
    emb1.reduce((sum, a, i) => sum + (a - emb2[i]) ** 2, 0)
  );
  
  console.log(`✅ Similarité cosinus: ${cosineSimilarity.toFixed(4)}`);
  console.log(`✅ Distance euclidienne: ${euclideanDistance.toFixed(4)}`);
  console.log(`✅ Dimensions vérifiées: ${emb1.length}/${ALBERT_CONFIG.dimensions}`);
}

async function runTests() {
  console.log('🎯 DÉBUT TESTS ALBERT API + PGVECTOR INTEGRATION\n');
  
  const testTexts = [
    "Paris est la capitale de la France",
    "London is the capital of England", 
    "Berlin ist die Hauptstadt von Deutschland",
    "Restaurant français traditionnel à Paris",
    "Modern British cuisine in London"
  ];
  
  const results = [];
  
  for (const text of testTexts) {
    const result = await testAlbertEmbedding(text);
    
    if (result.success) {
      const embedding = result.data.data[0].embedding;
      console.log(`✅ Embedding généré: ${embedding.length} dimensions`);
      console.log(`   Première valeurs: [${embedding.slice(0, 5).map(v => v.toFixed(4)).join(', ')}...]`);
      results.push(embedding);
    } else {
      console.log(`❌ Erreur: ${result.error}`);
      if (result.fallback) {
        console.log(`🔄 ${result.fallback}`);
      }
    }
  }
  
  // Test similarité entre embeddings
  await testSimilarity(results);
  
  console.log('\n🎉 TESTS TERMINÉS');
  
  // Résumé configuration pour Docker
  console.log('\n📋 CONFIGURATION RECOMMANDÉE POUR DOCKER:');
  console.log(`ALBERT_API_URL=${ALBERT_CONFIG.apiUrl}`);
  console.log(`ALBERT_API_TOKEN=${ALBERT_CONFIG.apiToken === 'test-token' ? 'YOUR_REAL_TOKEN' : '[CONFIGURÉ]'}`);
  console.log(`ALBERT_MODEL_EMBEDDING=${ALBERT_CONFIG.embeddingModel}`);
  console.log(`EMBEDDING_DIMENSION=${ALBERT_CONFIG.dimensions}`);
}

// Gestion des erreurs
process.on('unhandledRejection', (error) => {
  console.error('❌ Erreur non gérée:', error);
  process.exit(1);
});

// Exécution
runTests().catch(console.error);