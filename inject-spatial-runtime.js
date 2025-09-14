/**
 * Script d'injection runtime pour les extensions spatiales
 * Ce script se connecte au serveur Grist en cours d'exécution et injecte nos fonctionnalités
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

console.log('🚀 INJECTION RUNTIME DES EXTENSIONS SPATIALES');
console.log('=' .repeat(55));

// Test direct de nos extensions
async function testExtensionsLocally() {
    console.log('🧪 Test local des extensions...');
    
    try {
        // Test SpatialVectorService  
        const { SpatialVectorService } = require('./compiled-extensions/SpatialVectorService.js');
        const service = new SpatialVectorService();
        
        console.log('✅ SpatialVectorService instancié');
        console.log(`   Mode: ${service.simulationMode ? 'Simulation' : 'Albert API'}`);
        
        // Test embedding
        const embedding = await service.generateEmbedding('Test embedding');
        console.log(`   Embedding généré: ${embedding.length} dimensions`);
        
        // Test distance géographique
        const distance = service.calculateGeoDistance(48.8566, 2.3522, 48.8534, 2.3488);
        console.log(`   Distance Tour Eiffel -> Notre-Dame: ${Math.round(distance)}m`);
        
        // Test fonctions natives
        const functions = require('./compiled-extensions/NativeSpatialFunctions.js');
        console.log('✅ Fonctions natives:', Object.keys(functions).slice(0, 4).join(', ') + '...');
        
        // Test distance avec fonction native
        const nativeDistance = functions.GEO_DISTANCE('POINT(2.3522 48.8566)', 'POINT(2.3488 48.8534)');
        console.log(`   Test GEO_DISTANCE: ${Math.round(nativeDistance)}m`);
        
        return true;
    } catch (error) {
        console.log('❌ Erreur test local:', error.message);
        return false;
    }
}

// Injection dans le serveur Grist
async function injectIntoGrist() {
    console.log('\\n💉 Injection dans le serveur Grist...');
    
    // Pour l'instant, nous pouvons seulement vérifier que Grist fonctionne
    // L'injection complète nécessiterait de modifier le code serveur en direct
    
    try {
        const response = await new Promise((resolve, reject) => {
            const req = http.get('http://localhost:8485', resolve);
            req.on('error', reject);
            req.setTimeout(5000, () => reject(new Error('Timeout')));
        });
        
        console.log(`✅ Grist accessible (Status: ${response.statusCode})`);
        
        // Test si nos endpoints existent déjà (ils ne devraient pas)
        const spatialTest = await new Promise((resolve) => {
            const req = http.get('http://localhost:8485/api/docs/test/spatial/config', (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => resolve({ status: res.statusCode, data }));
            });
            req.on('error', () => resolve({ status: 0 }));
            req.setTimeout(3000, () => {
                req.destroy();
                resolve({ status: 0 });
            });
        });
        
        if (spatialTest.status === 404) {
            console.log('⚠️ Endpoints spatiaux non disponibles (injection requise)');
        } else if (spatialTest.status === 200) {
            console.log('🎉 Endpoints spatiaux déjà disponibles !');
            return true;
        } else {
            console.log(`⚠️ Status endpoint spatial: ${spatialTest.status}`);
        }
        
        return false;
    } catch (error) {
        console.log('❌ Erreur accès Grist:', error.message);
        return false;
    }
}

// Approche alternative: créer un serveur proxy qui ajoute nos endpoints
async function createSpatialProxy() {
    console.log('\\n🔄 Création d\\'un proxy spatial...');
    
    const express = require('express');
    const { createProxyMiddleware } = require('http-proxy-middleware');
    
    try {
        // Charger nos extensions
        const { setupSpatialRoutes } = require('./compiled-extensions/NativeSpatialApi.js');
        
        const app = express();
        app.use(express.json());
        
        // Ajouter nos routes spatiales
        setupSpatialRoutes(app);
        console.log('✅ Routes spatiales configurées');
        
        // Proxy pour toutes les autres requêtes vers Grist
        app.use('*', createProxyMiddleware({
            target: 'http://localhost:8485',
            changeOrigin: true,
            logLevel: 'silent'
        }));
        
        const server = app.listen(8486, () => {
            console.log('🎯 Proxy spatial lancé sur http://localhost:8486');
            console.log('   - Routes spatiales: /api/docs/{docId}/spatial/*'); 
            console.log('   - Toutes autres routes: proxy vers Grist:8485');
        });
        
        return server;
    } catch (error) {
        console.log('❌ Erreur création proxy:', error.message);
        return null;
    }
}

// Test des fonctionnalités via proxy
async function testSpatialProxy() {
    console.log('\\n🧪 Test des fonctionnalités spatiales...');
    
    const tests = [
        {
            name: 'Configuration spatiale',
            url: 'http://localhost:8486/api/docs/test/spatial/config'
        },
        {
            name: 'Test général',
            url: 'http://localhost:8486/api/docs/test/spatial/test',
            method: 'POST',
            data: '{}'
        },
        {
            name: 'Génération embedding',
            url: 'http://localhost:8486/api/docs/test/spatial/embedding',
            method: 'POST',
            data: JSON.stringify({ text: 'Test Paris monument' })
        },
        {
            name: 'Distance géographique',
            url: 'http://localhost:8486/api/docs/test/spatial/distance',
            method: 'POST',
            data: JSON.stringify({
                point1: 'POINT(2.3522 48.8566)',
                point2: 'POINT(2.3488 48.8534)'
            })
        }
    ];
    
    let successCount = 0;
    
    for (const test of tests) {
        try {
            const options = {
                method: test.method || 'GET',
                headers: { 'Content-Type': 'application/json' }
            };
            
            const response = await new Promise((resolve, reject) => {
                const req = http.request(test.url, options, resolve);
                req.on('error', reject);
                req.setTimeout(10000, () => reject(new Error('Timeout')));
                
                if (test.data) {
                    req.write(test.data);
                }
                req.end();
            });
            
            let responseData = '';
            response.on('data', chunk => responseData += chunk);
            
            await new Promise(resolve => {
                response.on('end', () => {
                    try {
                        if (response.statusCode === 200) {
                            const data = JSON.parse(responseData);
                            if (data.success) {
                                console.log(`✅ ${test.name}: Succès`);
                                
                                // Détails spécifiques
                                if (test.name === 'Distance géographique' && data.distance) {
                                    console.log(`   📏 ${Math.round(data.distance)}m`);
                                }
                                if (test.name === 'Génération embedding' && data.embedding) {
                                    console.log(`   🧮 ${data.embedding.length} dimensions`);
                                }
                                if (test.name === 'Configuration spatiale') {
                                    console.log(`   🔧 Albert: ${data.albertApiConfigured ? 'OK' : 'Simulation'}`);
                                }
                                
                                successCount++;
                            } else {
                                console.log(`⚠️ ${test.name}: ${data.error || 'Erreur inconnue'}`);
                            }
                        } else {
                            console.log(`❌ ${test.name}: Status ${response.statusCode}`);
                        }
                    } catch (e) {
                        console.log(`❌ ${test.name}: Parse error - ${responseData.substring(0, 100)}`);
                    }
                    resolve();
                });
            });
            
        } catch (error) {
            console.log(`❌ ${test.name}: ${error.message}`);
        }
        
        // Petite pause entre les tests
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    return successCount;
}

// Fonction principale
async function main() {
    console.log('📋 Étapes d\\'injection:');
    console.log('  1. Test local des extensions');  
    console.log('  2. Vérification serveur Grist');
    console.log('  3. Création proxy spatial'); 
    console.log('  4. Test des fonctionnalités');
    console.log('');
    
    // Étape 1
    const localTest = await testExtensionsLocally();
    if (!localTest) {
        console.log('❌ Échec des tests locaux - arrêt');
        return;
    }
    
    // Étape 2  
    const gristInject = await injectIntoGrist();
    if (gristInject) {
        console.log('🎉 Extensions déjà intégrées !');
        return;
    }
    
    // Étape 3
    const proxy = await createSpatialProxy();
    if (!proxy) {
        console.log('❌ Impossible de créer le proxy - arrêt');
        return;
    }
    
    // Petite pause pour laisser le proxy démarrer
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Étape 4
    const successCount = await testSpatialProxy();
    
    console.log('\\n🎯 RÉSULTATS INJECTION RUNTIME');
    console.log('=' .repeat(40));
    
    if (successCount >= 3) {
        console.log('🎉 Injection réussie !');
        console.log(`✅ ${successCount}/4 tests passés`);
        console.log('');
        console.log('🌐 Grist spatial disponible:');
        console.log('   - Interface: http://localhost:8486');
        console.log('   - API spatiale: http://localhost:8486/api/docs/{docId}/spatial/*');
        console.log('');
        console.log('📚 Fonctions disponibles:');
        console.log('   GEO_DISTANCE, GEO_AREA, GEO_CONTAINS, GEO_BUFFER');
        console.log('   GENERATE_EMBEDDING, SEARCH_SIMILAR, VECTOR_SIMILARITY, HYBRID_SEARCH');
        
        // Garder le proxy ouvert
        console.log('\\n⚡ Proxy spatial actif - Appuyez sur Ctrl+C pour arrêter');
        
    } else {
        console.log('⚠️ Injection partielle');
        console.log(`📊 ${successCount}/4 tests passés`);
        console.log('🔧 Vérifiez les logs ci-dessus pour diagnostiquer');
        
        proxy.close();
    }
}

// Démarrer si appelé directement
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { testExtensionsLocally, injectIntoGrist, createSpatialProxy };