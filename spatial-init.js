/**
 * Script d'initialisation pour les extensions spatiales/vectorielles dans Grist
 * Ce script est exécuté au démarrage du container pour injecter nos fonctionnalités
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 Initialisation des extensions spatiales pour Grist');
console.log('=' .repeat(60));

// Fonction pour injecter du code dans un fichier existant
function injectCodeIntoFile(filePath, searchPattern, codeToInject) {
    try {
        if (!fs.existsSync(filePath)) {
            console.log(`⚠️ Fichier non trouvé: ${filePath}`);
            return false;
        }

        let content = fs.readFileSync(filePath, 'utf8');
        
        if (content.includes(codeToInject)) {
            console.log(`✅ Code déjà injecté dans ${filePath}`);
            return true;
        }

        // Chercher le pattern et injecter le code
        if (content.includes(searchPattern)) {
            content = content.replace(searchPattern, searchPattern + '\n' + codeToInject);
            fs.writeFileSync(filePath, content);
            console.log(`✅ Code injecté dans ${filePath}`);
            return true;
        } else {
            console.log(`⚠️ Pattern non trouvé dans ${filePath}: ${searchPattern}`);
            return false;
        }
    } catch (error) {
        console.log(`❌ Erreur injection ${filePath}: ${error.message}`);
        return false;
    }
}

// Rechercher les fichiers principaux de Grist
function findGristFiles() {
    const possiblePaths = [
        '/grist/server.js',
        '/grist/_build/server.js', 
        '/grist/app/server/server.js',
        '/grist/lib/server.js'
    ];
    
    for (const filePath of possiblePaths) {
        if (fs.existsSync(filePath)) {
            console.log(`📁 Fichier serveur trouvé: ${filePath}`);
            return filePath;
        }
    }
    
    console.log('❌ Aucun fichier serveur Grist trouvé');
    return null;
}

// Code à injecter pour charger nos extensions
const spatialExtensionCode = `
// === EXTENSIONS SPATIALES INJECTÉES ===
try {
    const spatialFunctions = require('/grist/spatial-functions.js');
    const { setupSpatialRoutes } = require('/grist/spatial-api.js');
    
    console.log('🗺️ Chargement extensions spatiales...');
    
    // Ajouter les fonctions spatiales aux fonctions globales
    if (typeof global !== 'undefined') {
        Object.assign(global, spatialFunctions);
        console.log('✅ Fonctions spatiales ajoutées:', Object.keys(spatialFunctions));
    }
    
    // Si on trouve l'app Express, ajouter les routes spatiales
    if (typeof app !== 'undefined' && app.use) {
        setupSpatialRoutes(app);
        console.log('✅ Routes API spatiales configurées');
    }
    
    console.log('🚀 Extensions spatiales chargées avec succès !');
    
} catch (error) {
    console.log('❌ Erreur chargement extensions spatiales:', error.message);
}
// === FIN EXTENSIONS SPATIALES ===
`;

// Fonction principale d'injection
async function injectSpatialExtensions() {
    console.log('💉 Injection des extensions spatiales dans Grist...');
    
    // Vérifier que nos fichiers d'extension existent
    const extensionFiles = [
        '/grist/spatial-functions.js',
        '/grist/spatial-api.js'
    ];
    
    for (const file of extensionFiles) {
        if (!fs.existsSync(file)) {
            console.log(`❌ Fichier d'extension manquant: ${file}`);
            return false;
        }
    }
    
    // Trouver le fichier serveur principal
    const serverFile = findGristFiles();
    if (!serverFile) {
        return false;
    }
    
    // Injecter le code d'initialisation
    const patterns = [
        'const express = require(\'express\')',
        'require(\'express\')',
        'const app = express()',
        'app.listen(',
        'server.listen('
    ];
    
    let injected = false;
    for (const pattern of patterns) {
        if (injectCodeIntoFile(serverFile, pattern, spatialExtensionCode)) {
            injected = true;
            break;
        }
    }
    
    if (!injected) {
        // Dernière tentative: ajouter en début de fichier
        try {
            const content = fs.readFileSync(serverFile, 'utf8');
            const newContent = spatialExtensionCode + '\n' + content;
            fs.writeFileSync(serverFile, newContent);
            console.log('✅ Code injecté en début de fichier');
            injected = true;
        } catch (error) {
            console.log('❌ Échec injection finale:', error.message);
        }
    }
    
    return injected;
}

// Exécution si appelé directement
if (require.main === module) {
    (async () => {
        const success = await injectSpatialExtensions();
        
        if (success) {
            console.log('🎉 Extensions spatiales prêtes !');
            console.log('📋 Fonctionnalités disponibles:');
            console.log('   - API REST: /api/docs/{docId}/spatial/*');
            console.log('   - Fonctions: GEO_DISTANCE, GENERATE_EMBEDDING, etc.');
            console.log('   - Service vectoriel Albert API intégré');
        } else {
            console.log('❌ Échec injection des extensions');
        }
        
        console.log('=' .repeat(60));
    })();
}

module.exports = { injectSpatialExtensions };