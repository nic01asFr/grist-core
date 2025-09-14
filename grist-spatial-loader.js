#!/usr/bin/env node

/**
 * Chargeur simplifié pour les extensions spatiales dans Grist
 */

console.log('🚀 CHARGEMENT DES EXTENSIONS SPATIALES');
console.log('=' .repeat(50));

// Script à exécuter dans le container
const loaderScript = `
console.log('💉 Chargement des extensions spatiales...');

try {
    // Charger nos extensions
    const spatialFunctions = require('/grist/spatial-extensions/NativeSpatialFunctions.js');
    const { SpatialVectorService } = require('/grist/spatial-extensions/SpatialVectorService.js');
    
    // Créer une instance globale du service
    global.spatialService = new SpatialVectorService();
    console.log('✅ Service spatial créé (mode: ' + (global.spatialService.simulationMode ? 'simulation' : 'Albert API') + ')');
    
    // Ajouter les fonctions au contexte global
    Object.keys(spatialFunctions).forEach(funcName => {
        global[funcName] = spatialFunctions[funcName];
        console.log('   + ' + funcName);
    });
    
    console.log('✅ ' + Object.keys(spatialFunctions).length + ' fonctions spatiales chargées');
    
    // Test rapide
    console.log('\\n🧪 Tests rapides:');
    
    // Test GEO_DISTANCE
    const distance = global.GEO_DISTANCE('POINT(2.3522 48.8566)', 'POINT(2.3488 48.8534)');
    console.log('   GEO_DISTANCE Tour Eiffel <-> Notre-Dame: ' + Math.round(distance) + 'm');
    
    // Test VECTOR_SIMILARITY  
    const sim = global.VECTOR_SIMILARITY('[1,0,0]', '[0.5,0.5,0]');
    console.log('   VECTOR_SIMILARITY: ' + sim.toFixed(3));
    
    // Test GENERATE_EMBEDDING (async)
    global.GENERATE_EMBEDDING('Test embedding').then(result => {
        const embedding = JSON.parse(result);
        console.log('   GENERATE_EMBEDDING: ' + embedding.length + ' dimensions');
    }).catch(err => {
        console.log('   GENERATE_EMBEDDING erreur: ' + err.message);
    });
    
    console.log('\\n✅ Extensions spatiales prêtes !');
    console.log('📋 Fonctions disponibles:');
    console.log('   GEO_DISTANCE, GEO_AREA, GEO_CONTAINS, GEO_BUFFER');
    console.log('   GENERATE_EMBEDDING, SEARCH_SIMILAR, VECTOR_SIMILARITY, HYBRID_SEARCH');
    
} catch (error) {
    console.log('❌ Erreur chargement: ' + error.message);
    console.log('Stack: ' + error.stack);
}
`;

const fs = require('fs');
const { execSync } = require('child_process');

// Écrire le script
fs.writeFileSync('/tmp/grist-spatial-loader.js', loaderScript);
console.log('📝 Script de chargement créé');

// Copier dans le container
try {
    execSync('docker cp /tmp/grist-spatial-loader.js grist-spatial-test:/grist/spatial-loader.js');
    console.log('✅ Script copié dans le container');
} catch (error) {
    console.log('❌ Erreur copie:', error.message);
    process.exit(1);
}

// Exécuter le chargement
console.log('💉 Exécution du chargement...\n');
try {
    const output = execSync('docker exec grist-spatial-test node /grist/spatial-loader.js', { encoding: 'utf8' });
    console.log(output);
} catch (error) {
    console.log('Sortie:', error.stdout);
    console.log('❌ Erreur:', error.message);
}

// Créer un fichier de démarrage personnalisé
console.log('\n📄 Création du script de démarrage personnalisé...');

const startupScript = `#!/bin/bash
echo "🚀 Démarrage de Grist avec extensions spatiales..."

# Charger les extensions au démarrage
node /grist/spatial-loader.js

# Démarrer Grist normalement
exec /usr/local/bin/docker-entrypoint.sh
`;

fs.writeFileSync('/tmp/grist-spatial-startup.sh', startupScript);

try {
    execSync('docker cp /tmp/grist-spatial-startup.sh grist-spatial-test:/grist/spatial-startup.sh');
    execSync('docker exec grist-spatial-test chmod +x /grist/spatial-startup.sh');
    console.log('✅ Script de démarrage créé');
} catch (error) {
    console.log('⚠️ Erreur création script démarrage:', error.message);
}

console.log('\n🎯 INSTRUCTIONS D\'UTILISATION');
console.log('=' .repeat(50));
console.log('1. Accédez à Grist: http://localhost:8485');
console.log('2. Créez un nouveau document ou ouvrez-en un existant');
console.log('3. Dans une cellule, cliquez sur l\'icône de formule (=)');
console.log('4. Essayez ces formules:');
console.log('');
console.log('   Calcul de distance:');
console.log('   =GEO_DISTANCE("POINT(2.3522 48.8566)", "POINT(2.3488 48.8534)")');
console.log('');
console.log('   Génération d\'embedding (retourne JSON):');
console.log('   =GENERATE_EMBEDDING("Mon texte à vectoriser")');
console.log('');
console.log('   Similarité entre vecteurs:');
console.log('   =VECTOR_SIMILARITY("[1,0,0]", "[0.5,0.5,0]")');
console.log('');
console.log('   Calcul d\'aire:');
console.log('   =GEO_AREA("POLYGON((0 0,1 0,1 1,0 1,0 0))")');
console.log('');
console.log('💡 Note: Les fonctions async comme GENERATE_EMBEDDING peuvent');
console.log('   prendre un moment pour s\'exécuter la première fois.');
console.log('');
console.log('🔄 Pour redémarrer Grist avec les extensions:');
console.log('   docker restart grist-spatial-test');
console.log('');
console.log('📊 Pour créer des colonnes spatiales:');
console.log('   1. Ajoutez une colonne de type "Text"');
console.log('   2. Entrez des géométries WKT (ex: POINT(x y))');
console.log('   3. Utilisez les fonctions GEO_* dans d\'autres colonnes');
console.log('');
console.log('🧮 Pour créer des colonnes vectorielles:');
console.log('   1. Ajoutez une colonne avec formule =GENERATE_EMBEDDING($TextColumn)');
console.log('   2. Utilisez VECTOR_SIMILARITY pour comparer');
console.log('   3. Utilisez SEARCH_SIMILAR pour rechercher');