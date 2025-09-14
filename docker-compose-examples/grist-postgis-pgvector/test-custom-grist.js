/**
 * Test de notre version Grist modifiée avec extensions spatiales/vectorielles
 */

const http = require('http');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

const GRIST_CUSTOM_URL = 'http://localhost:8485';

console.log('🚀 TEST GRIST SPATIAL MODIFIÉ');
console.log('=' .repeat(50));

async function waitForGrist(maxAttempts = 30) {
    console.log(`⏳ Attente du service Grist modifié ${GRIST_CUSTOM_URL}...`);
    
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await new Promise((resolve, reject) => {
                const req = http.get(GRIST_CUSTOM_URL, resolve);
                req.on('error', reject);
                req.setTimeout(5000, () => reject(new Error('Timeout')));
            });
            
            if (response.statusCode === 200 || response.statusCode === 302) {
                console.log(`✅ Grist modifié disponible après ${i + 1} tentatives`);
                return true;
            }
        } catch (error) {
            if (i < maxAttempts - 1) {
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
        }
    }
    
    console.log('❌ Grist modifié non disponible');
    return false;
}

async function testSpatialEndpoints() {
    console.log('\\n🗺️ Test des endpoints spatiaux personnalisés...');
    
    const spatialTests = [
        {
            name: 'Endpoint embedding spatial',
            method: 'POST',
            url: `${GRIST_CUSTOM_URL}/api/docs/test/spatial/embedding`,
            data: JSON.stringify({ text: "Test embedding spatial" }),
            headers: { 'Content-Type': 'application/json' }
        },
        {
            name: 'Endpoint recherche vectorielle',
            method: 'POST', 
            url: `${GRIST_CUSTOM_URL}/api/docs/test/spatial/similarity/search`,
            data: JSON.stringify({ 
                query: "recherche test",
                limit: 5 
            }),
            headers: { 'Content-Type': 'application/json' }
        },
        {
            name: 'Endpoint distance géographique',
            method: 'POST',
            url: `${GRIST_CUSTOM_URL}/api/docs/test/spatial/distance`,
            data: JSON.stringify({
                point1: "POINT(2.3522 48.8566)",
                point2: "POINT(2.3488 48.8534)"
            }),
            headers: { 'Content-Type': 'application/json' }
        }
    ];
    
    for (const test of spatialTests) {
        try {
            const response = await new Promise((resolve, reject) => {
                const req = http.request({
                    hostname: 'localhost',
                    port: 8485,
                    path: test.url.replace(GRIST_CUSTOM_URL, ''),
                    method: test.method,
                    headers: test.headers
                }, resolve);
                
                req.on('error', reject);
                req.setTimeout(10000, () => reject(new Error('Timeout')));
                
                if (test.data) {
                    req.write(test.data);
                }
                req.end();
            });
            
            if (response.statusCode === 404) {
                console.log(`⚠️ ${test.name}: Endpoint non trouvé (version non modifiée)`);
            } else if (response.statusCode < 400) {
                console.log(`✅ ${test.name}: Status ${response.statusCode} (endpoint disponible !)`);
            } else {
                console.log(`⚠️ ${test.name}: Status ${response.statusCode}`);
            }
        } catch (error) {
            console.log(`❌ ${test.name}: ${error.message}`);
        }
    }
}

async function testUIModifications() {
    console.log('\\n🎨 Test modifications interface utilisateur...');
    
    try {
        const response = await new Promise((resolve, reject) => {
            const req = http.get(`${GRIST_CUSTOM_URL}/static/`, resolve);
            req.on('error', reject);
            req.setTimeout(10000, () => reject(new Error('Timeout')));
        });
        
        let data = '';
        response.on('data', chunk => data += chunk);
        response.on('end', () => {
            if (data.includes('Geometry') || data.includes('Vector') || data.includes('MapWidget')) {
                console.log('✅ Modifications interface détectées (types spatiaux présents)');
            } else {
                console.log('⚠️ Modifications interface non détectées');
            }
        });
    } catch (error) {
        console.log('❌ Impossible de tester l\\'interface');
    }
}

async function showExpectedFeatures() {
    console.log('\\n🎯 FONCTIONNALITÉS ATTENDUES DANS LA VERSION MODIFIÉE');
    console.log('='.repeat(55));
    
    const expectedFeatures = [
        '🔹 Types de colonnes supplémentaires:',
        '   - Type "Geometry" (édition WKT/GeoJSON)',
        '   - Type "Vector" (embeddings 1024 dimensions)',
        '',
        '🔹 Widgets spécialisés:',
        '   - MapWidget (visualisation géographique)',
        '   - GeometryEditor (édition géométries)',
        '   - VectorEditor (gestion embeddings)',
        '',
        '🔹 Nouvelles formules disponibles:',
        '   - GEO_DISTANCE(point1, point2)',
        '   - GEO_AREA(geometry)',
        '   - GEO_CONTAINS(geom1, geom2)',
        '   - GENERATE_EMBEDDING(text)',
        '   - SEARCH_SIMILAR(vector, data)',
        '   - HYBRID_SEARCH(query, data)',
        '',
        '🔹 Configuration API:',
        '   - Section paramètres pour clé API Albert',
        '   - Configuration URL service embedding',
        '',
        '🔹 Endpoints API spatiaux:',
        '   - /api/docs/{docId}/spatial/embedding',
        '   - /api/docs/{docId}/spatial/similarity/search',
        '   - /api/docs/{docId}/spatial/distance',
        '   - /api/docs/{docId}/spatial/hybrid/search'
    ];
    
    expectedFeatures.forEach(feature => console.log(`   ${feature}`));
}

async function runCustomGristTest() {
    console.log(`🌐 URL Grist modifié: ${GRIST_CUSTOM_URL}`);
    
    // Vérifier que le container fonctionne
    try {
        const { stdout } = await execAsync('docker ps --filter "name=grist-spatial-custom" --format "table {{.Names}}\\t{{.Status}}"');
        console.log(`📋 Status container modifié:\\n${stdout}`);
    } catch (error) {
        console.log('⚠️ Container Grist modifié non trouvé - en cours de construction ?');
    }
    
    const gristReady = await waitForGrist();
    
    if (gristReady) {
        await testSpatialEndpoints();
        await testUIModifications();
        
        console.log('\\n🚀 RÉSULTAT TEST VERSION MODIFIÉE');
        console.log('='.repeat(45));
        console.log('✅ Container Grist modifié opérationnel');
        console.log('📋 Accès: http://localhost:8485');
        
    } else {
        console.log('❌ Container Grist modifié non accessible');
        console.log('💡 Vérifiez que la construction Docker est terminée');
    }
    
    await showExpectedFeatures();
}

// Exécuter le test
runCustomGristTest().catch(console.error);