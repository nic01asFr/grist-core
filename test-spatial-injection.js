/**
 * Test de l'approche d'injection des extensions spatiales dans Grist officiel
 */

const http = require('http');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

const GRIST_INJECTION_URL = 'http://localhost:8485';

console.log('🧪 TEST INJECTION EXTENSIONS SPATIALES DANS GRIST');
console.log('=' .repeat(60));

async function waitForGrist(maxAttempts = 20) {
    console.log(`⏳ Attente du service Grist injecté ${GRIST_INJECTION_URL}...`);
    
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await new Promise((resolve, reject) => {
                const req = http.get(GRIST_INJECTION_URL, resolve);
                req.on('error', reject);
                req.setTimeout(5000, () => reject(new Error('Timeout')));
            });
            
            if (response.statusCode === 200 || response.statusCode === 302) {
                console.log(`✅ Grist injecté disponible après ${i + 1} tentatives`);
                return true;
            }
        } catch (error) {
            if (i < maxAttempts - 1) {
                console.log(`   Tentative ${i + 1}/${maxAttempts} échouée, retry...`);
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        }
    }
    
    console.log('❌ Grist injecté non disponible');
    return false;
}

async function testSpatialEndpoints() {
    console.log('\\n🗺️ Test des endpoints API spatiaux injectés...');
    
    const spatialTests = [
        {
            name: 'Configuration spatiale',
            method: 'GET',
            url: `${GRIST_INJECTION_URL}/api/docs/test/spatial/config`,
            expected: 'spatialEnabled'
        },
        {
            name: 'Test des fonctionnalités',
            method: 'POST', 
            url: `${GRIST_INJECTION_URL}/api/docs/test/spatial/test`,
            data: JSON.stringify({}),
            headers: { 'Content-Type': 'application/json' },
            expected: 'embedding'
        },
        {
            name: 'Génération embedding',
            method: 'POST',
            url: `${GRIST_INJECTION_URL}/api/docs/test/spatial/embedding`,
            data: JSON.stringify({ text: "Test embedding injection" }),
            headers: { 'Content-Type': 'application/json' },
            expected: 'embedding'
        },
        {
            name: 'Distance géographique',
            method: 'POST',
            url: `${GRIST_INJECTION_URL}/api/docs/test/spatial/distance`,
            data: JSON.stringify({
                point1: "POINT(2.3522 48.8566)",  // Tour Eiffel
                point2: "POINT(2.3488 48.8534)"   // Notre-Dame  
            }),
            headers: { 'Content-Type': 'application/json' },
            expected: 'distance'
        },
        {
            name: 'Recherche vectorielle',
            method: 'POST',
            url: `${GRIST_INJECTION_URL}/api/docs/test/spatial/similarity/search`,
            data: JSON.stringify({
                query: "Paris monument historique",
                data: [
                    { text: "Tour Eiffel", embedding: Array.from({length: 1024}, () => Math.random()) },
                    { text: "Notre-Dame", embedding: Array.from({length: 1024}, () => Math.random()) }
                ],
                limit: 2
            }),
            headers: { 'Content-Type': 'application/json' },
            expected: 'results'
        }
    ];
    
    let successCount = 0;
    
    for (const test of spatialTests) {
        try {
            const response = await new Promise((resolve, reject) => {
                const options = {
                    hostname: 'localhost',
                    port: 8485,
                    path: test.url.replace(GRIST_INJECTION_URL, ''),
                    method: test.method,
                    headers: test.headers || {}
                };
                
                const req = http.request(options, resolve);
                req.on('error', reject);
                req.setTimeout(15000, () => reject(new Error('Timeout')));
                
                if (test.data) {
                    req.write(test.data);
                }
                req.end();
            });
            
            let responseData = '';
            response.on('data', chunk => responseData += chunk);
            
            await new Promise((resolve) => {
                response.on('end', () => {
                    try {
                        if (response.statusCode === 404) {
                            console.log(`❌ ${test.name}: Endpoint non trouvé (injection échouée)`);
                        } else if (response.statusCode >= 400) {
                            console.log(`⚠️ ${test.name}: Status ${response.statusCode}`);
                            if (responseData) {
                                console.log(`     Réponse: ${responseData.substring(0, 200)}`);
                            }
                        } else {
                            const data = JSON.parse(responseData);
                            if (data.success && (test.expected ? data[test.expected] !== undefined : true)) {
                                console.log(`✅ ${test.name}: Succès !`);
                                successCount++;
                                
                                // Log des détails importants
                                if (test.name === 'Configuration spatiale') {
                                    console.log(`     🔧 Albert API: ${data.albertApiConfigured ? 'Configuré' : 'Non configuré'}`);
                                    console.log(`     🎯 Mode: ${data.simulationMode ? 'Simulation' : 'Albert API'}`);
                                }
                                if (test.name === 'Distance géographique' && data.distance) {
                                    console.log(`     📏 Distance Tour Eiffel <-> Notre-Dame: ${Math.round(data.distance)}m`);
                                }
                                if (test.name === 'Génération embedding' && data.embedding) {
                                    console.log(`     🧮 Embedding généré: ${data.embedding.length} dimensions`);
                                }
                            } else {
                                console.log(`⚠️ ${test.name}: Réponse inattendue`);
                                console.log(`     ${JSON.stringify(data).substring(0, 150)}...`);
                            }
                        }
                    } catch (e) {
                        console.log(`❌ ${test.name}: Erreur parsing - ${responseData.substring(0, 100)}`);
                    }
                    resolve();
                });
            });
            
        } catch (error) {
            console.log(`❌ ${test.name}: ${error.message}`);
        }
    }
    
    return successCount;
}

async function testContainerStatus() {
    console.log('\\n🐳 Status des containers d\\'injection...');
    
    try {
        const { stdout } = await execAsync('docker ps --filter "name=grist-" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"');
        console.log(stdout);
        
        // Logs du container Grist injecté
        try {
            const { stdout: logs } = await execAsync('docker logs --tail 10 grist-spatial-injected 2>&1 | grep -E "(💉|✅|❌|🚀)"');
            if (logs.trim()) {
                console.log('\\n📋 Logs d\\'injection récents:');
                logs.trim().split('\\n').forEach(line => console.log(`   ${line}`));
            }
        } catch (e) {
            console.log('   ⚠️ Pas de logs d\\'injection trouvés');
        }
        
    } catch (error) {
        console.log('❌ Impossible de récupérer le status des containers');
    }
}

async function runInjectionTest() {
    console.log(`🌐 URL Grist injecté: ${GRIST_INJECTION_URL}`);
    
    await testContainerStatus();
    
    const gristReady = await waitForGrist();
    
    if (gristReady) {
        const successCount = await testSpatialEndpoints();
        
        console.log('\\n🎯 RÉSULTATS TEST INJECTION');
        console.log('='.repeat(40));
        
        if (successCount >= 3) {
            console.log('🎉 Injection réussie ! Extensions spatiales opérationnelles');
            console.log(`✅ ${successCount}/5 endpoints fonctionnels`);
            console.log('📋 Accès Grist modifié: http://localhost:8485');
        } else if (successCount > 0) {
            console.log('⚠️ Injection partielle');  
            console.log(`📊 ${successCount}/5 endpoints fonctionnels`);
            console.log('🔧 Vérifiez les logs du container pour diagnostiquer');
        } else {
            console.log('❌ Injection échouée - aucun endpoint spatial disponible');
            console.log('💡 Vérifiez que les fichiers d\\'extension sont bien montés');
        }
        
    } else {
        console.log('❌ Container Grist injecté non accessible');
        console.log('💡 Vérifiez: docker-compose -f docker-compose-injection.yml logs');
    }
    
    console.log('\\n🔗 Commandes utiles:');
    console.log('   docker-compose -f docker-compose-injection.yml logs grist-spatial-injected');
    console.log('   docker exec -it grist-spatial-injected ls -la /grist/spatial-extensions/');
    console.log('   curl http://localhost:8485/api/docs/test/spatial/config');
}

// Exécution du test
runInjectionTest().catch(console.error);