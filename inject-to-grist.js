#!/usr/bin/env node

/**
 * Script pour injecter les extensions spatiales dans Grist en cours d'exécution
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 INJECTION DES EXTENSIONS SPATIALES DANS GRIST');
console.log('=' .repeat(60));

// Script d'injection à exécuter dans le container
const injectionScript = `
const fs = require('fs');
const path = require('path');

console.log('💉 Début de l\\'injection dans Grist...');

// Charger nos extensions
const spatialFunctions = require('/grist/spatial-extensions/NativeSpatialFunctions.js');
const { setupSpatialRoutes } = require('/grist/spatial-extensions/NativeSpatialApi.js');
const { SpatialVectorService } = require('/grist/spatial-extensions/SpatialVectorService.js');

// Créer une instance du service
global.spatialService = new SpatialVectorService();

// Ajouter les fonctions spatiales aux fonctions globales
Object.assign(global, spatialFunctions);

console.log('✅ Fonctions spatiales ajoutées:', Object.keys(spatialFunctions));

// Chercher le serveur Express de Grist
function findExpressApp() {
    // Parcourir les modules chargés pour trouver l'app Express
    const keys = Object.keys(require.cache);
    for (const key of keys) {
        const mod = require.cache[key];
        if (mod && mod.exports && mod.exports.app && typeof mod.exports.app.use === 'function') {
            return mod.exports.app;
        }
    }
    
    // Essayer de trouver via le contexte global
    if (global.app && typeof global.app.use === 'function') {
        return global.app;
    }
    
    // Chercher dans les propriétés du module principal
    if (process.mainModule && process.mainModule.exports) {
        if (process.mainModule.exports.app) {
            return process.mainModule.exports.app;
        }
    }
    
    return null;
}

// Trouver et patcher l'app Express
const app = findExpressApp();
if (app) {
    console.log('✅ App Express trouvée, ajout des routes spatiales...');
    setupSpatialRoutes(app);
    console.log('✅ Routes spatiales configurées !');
} else {
    console.log('⚠️ App Express non trouvée, création d\\'un serveur proxy...');
    
    // Créer un serveur proxy sur un port différent
    const express = require('express');
    const proxyApp = express();
    proxyApp.use(express.json());
    
    // Ajouter nos routes spatiales
    setupSpatialRoutes(proxyApp);
    
    // Démarrer le proxy
    const proxyPort = 8487;
    proxyApp.listen(proxyPort, () => {
        console.log(\`🌐 Serveur proxy spatial lancé sur le port \${proxyPort}\`);
        console.log(\`   Endpoints disponibles: http://localhost:\${proxyPort}/api/docs/{docId}/spatial/*\`);
    });
}

// Patcher les fonctions de formule de Grist
try {
    // Chercher le module de formules
    const formulaModules = Object.keys(require.cache).filter(k => 
        k.includes('formula') || k.includes('Formula') || k.includes('functions')
    );
    
    if (formulaModules.length > 0) {
        console.log(\`📝 \${formulaModules.length} modules de formules trouvés\`);
        
        formulaModules.forEach(modPath => {
            const mod = require.cache[modPath];
            if (mod && mod.exports) {
                // Ajouter nos fonctions
                Object.assign(mod.exports, spatialFunctions);
                console.log(\`✅ Fonctions ajoutées à \${path.basename(modPath)}\`);
            }
        });
    } else {
        console.log('⚠️ Modules de formules non trouvés');
    }
} catch (error) {
    console.log('⚠️ Erreur patch formules:', error.message);
}

// Enregistrer les fonctions pour qu'elles soient disponibles dans les formules
if (global.grist && global.grist.functions) {
    Object.assign(global.grist.functions, spatialFunctions);
    console.log('✅ Fonctions ajoutées à grist.functions');
}

// Test rapide
console.log('\\n🧪 Test rapide des fonctions:');
try {
    const distance = spatialFunctions.GEO_DISTANCE('POINT(2.3522 48.8566)', 'POINT(2.3488 48.8534)');
    console.log(\`   GEO_DISTANCE: \${Math.round(distance)}m\`);
    
    const embedding = spatialFunctions.GENERATE_EMBEDDING('Test').then(result => {
        const parsed = JSON.parse(result);
        console.log(\`   GENERATE_EMBEDDING: \${parsed.length} dimensions\`);
    });
} catch (error) {
    console.log(\`   Erreur test: \${error.message}\`);
}

console.log('\\n✅ Injection terminée !');
console.log('📋 Fonctions disponibles dans Grist:');
Object.keys(spatialFunctions).forEach(func => {
    console.log(\`   - \${func}()\`);
});
`;

// Écrire le script dans un fichier temporaire
fs.writeFileSync('/tmp/inject-spatial.js', injectionScript);

console.log('📝 Script d\'injection créé');
console.log('🔄 Copie dans le container...');

// Copier le script dans le container
const { execSync } = require('child_process');
try {
    execSync('docker cp /tmp/inject-spatial.js grist-spatial-test:/tmp/inject-spatial.js');
    console.log('✅ Script copié dans le container');
} catch (error) {
    console.log('❌ Erreur copie:', error.message);
    process.exit(1);
}

console.log('💉 Exécution de l\'injection...\n');

// Exécuter le script dans le container
try {
    const output = execSync('docker exec grist-spatial-test node /tmp/inject-spatial.js', { encoding: 'utf8' });
    console.log(output);
} catch (error) {
    console.log('❌ Erreur injection:', error.message);
}

console.log('\n🧪 Test des endpoints après injection...');

// Tester les endpoints
const http = require('http');

async function testEndpoint(name, path, method = 'GET', data = null) {
    return new Promise((resolve) => {
        const options = {
            hostname: 'localhost',
            port: 8485,
            path: path,
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        
        const req = http.request(options, (res) => {
            let responseData = '';
            res.on('data', chunk => responseData += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    console.log(`✅ ${name}: OK`);
                } else if (res.statusCode === 404) {
                    console.log(`⚠️ ${name}: Non trouvé (essayer le proxy sur le port 8487)`);
                } else {
                    console.log(`❌ ${name}: Status ${res.statusCode}`);
                }
                resolve();
            });
        });
        
        req.on('error', (error) => {
            console.log(`❌ ${name}: ${error.message}`);
            resolve();
        });
        
        if (data) {
            req.write(JSON.stringify(data));
        }
        
        req.end();
    });
}

// Tester les endpoints
(async () => {
    await testEndpoint('Configuration', '/api/docs/test/spatial/config');
    await testEndpoint('Test général', '/api/docs/test/spatial/test', 'POST', {});
    await testEndpoint('Embedding', '/api/docs/test/spatial/embedding', 'POST', { text: 'Test' });
    
    console.log('\n🎯 RÉSUMÉ');
    console.log('=' .repeat(40));
    console.log('✅ Extensions spatiales injectées dans Grist');
    console.log('📋 Accès:');
    console.log('   - Interface Grist: http://localhost:8485');
    console.log('   - API spatiale: http://localhost:8485/api/docs/{docId}/spatial/*');
    console.log('   - Si les endpoints ne fonctionnent pas, essayer le proxy: http://localhost:8487');
    console.log('\n💡 Pour utiliser les fonctions dans Grist:');
    console.log('   1. Créez un nouveau document');
    console.log('   2. Dans une cellule de formule, utilisez:');
    console.log('      =GEO_DISTANCE("POINT(2.3522 48.8566)", "POINT(2.3488 48.8534)")');
    console.log('      =GENERATE_EMBEDDING("Votre texte")');
    console.log('      =VECTOR_SIMILARITY($VectorCol1, $VectorCol2)');
})();