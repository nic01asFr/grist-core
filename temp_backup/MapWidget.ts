import {GristDoc} from 'app/client/components/GristDoc';
import {ViewFieldRec} from 'app/client/models/entities/ViewFieldRec';
import {NewAbstractWidget} from 'app/client/widgets/NewAbstractWidget';
import {dom, DomElementArg, styled} from 'grainjs';
import * as L from 'leaflet';

/**
 * MapWidget - Widget de visualisation interactive pour les données géospatiales
 * 
 * Fonctionnalités :
 * - Affichage de points, lignes, polygones sur carte interactive
 * - Support des formats WKT (POINT, LINESTRING, POLYGON, etc.)
 * - Clustering automatique des points proches
 * - Popups avec informations des enregistrements
 * - Zoom automatique sur les données
 * - Intégration avec la sélection Grist
 */
export class MapWidget extends NewAbstractWidget {
  protected map: L.Map | null = null;
  private geometryLayer: L.LayerGroup | null = null;
  private clusterGroup: L.MarkerClusterGroup | null = null;
  private mapContainer: HTMLElement | null = null;

  constructor(field: ViewFieldRec, opts: {gristDoc: GristDoc}) {
    super(field, opts);
    
    // Observer les changements de données pour mettre à jour la carte
    this.autoDispose(this.field.viewData().addListener(() => this.updateMap()));
    
    // Observer la sélection pour synchroniser avec la carte
    this.autoDispose(this.field.viewSection().viewInstance().cursor.currentPosition.addListener(
      () => this.updateSelection()
    ));
  }

  public buildDom(): DomElementArg {
    return MapContainer(
      dom('div.map-widget',
        {style: 'height: 400px; width: 100%;'},
        dom.onDispose(() => this.disposeMap()),
        (elem: HTMLElement) => {
          this.mapContainer = elem;
          this.initializeMap();
        }
      ),
      
      // Contrôles de la carte
      dom('div.map-controls',
        dom('button.map-btn', '🌍 Centrer',
          dom.on('click', () => this.fitBounds())
        ),
        dom('button.map-btn', '📍 Cluster',
          dom.on('click', () => this.toggleClustering())
        ),
        dom('button.map-btn', '📊 Heatmap', 
          dom.on('click', () => this.toggleHeatmap())
        ),
        dom('button.map-btn', '⚙️ Styles',
          dom.on('click', () => this.openStyleEditor())
        )
      )
    );
  }

  /**
   * Initialise la carte Leaflet
   */
  private initializeMap(): void {
    if (!this.mapContainer) return;

    // Créer la carte avec OpenStreetMap par défaut
    this.map = L.map(this.mapContainer, {
      center: [46.603354, 1.888334], // Centre de la France par défaut
      zoom: 6,
      zoomControl: true,
      attributionControl: true
    });

    // Ajouter le layer de base (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(this.map);

    // Créer les layers pour les géométries
    this.geometryLayer = L.layerGroup().addTo(this.map);
    
    // Initialiser le clustering si disponible
    if (typeof L.markerClusterGroup === 'function') {
      this.clusterGroup = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 50
      });
    }

    // Charger les données initiales
    this.updateMap();
  }

  /**
   * Met à jour la carte avec les données actuelles
   */
  private async updateMap(): Promise<void> {
    if (!this.map || !this.geometryLayer) return;

    // Nettoyer les markers existants
    this.geometryLayer.clearLayers();
    if (this.clusterGroup) {
      this.clusterGroup.clearLayers();
    }

    // Récupérer les données de géométrie
    const geometryData = this.field.viewData().peek();
    const allRecords = this.field.viewSection().viewInstance().viewData.peek();

    if (!geometryData || !allRecords) return;

    const geometries: Array<{wkt: string, record: any, rowId: number}> = [];
    
    // Associer géométries avec records complets
    geometryData.forEach((wkt: string, index: number) => {
      if (wkt && typeof wkt === 'string' && wkt.trim() !== '') {
        const record = allRecords.get(index);
        if (record) {
          geometries.push({ wkt: wkt.trim(), record, rowId: record.id() });
        }
      }
    });

    // Convertir et afficher chaque géométrie
    for (const {wkt, record, rowId} of geometries) {
      try {
        const layer = this.parseWKTToLayer(wkt, record, rowId);
        if (layer) {
          if (this.clusterGroup && layer instanceof L.Marker) {
            this.clusterGroup.addLayer(layer);
          } else {
            this.geometryLayer.addLayer(layer);
          }
        }
      } catch (error) {
        console.warn(`Impossible de parser la géométrie WKT: ${wkt}`, error);
      }
    }

    // Ajouter le cluster group à la carte si nécessaire
    if (this.clusterGroup && this.clusterGroup.getLayers().length > 0) {
      this.map.addLayer(this.clusterGroup);
    }

    // Ajuster la vue pour inclure toutes les géométries
    this.fitBounds();
  }

  /**
   * Parse une chaîne WKT et retourne un layer Leaflet
   */
  private parseWKTToLayer(wkt: string, record: any, rowId: number): L.Layer | null {
    const wktUpper = wkt.toUpperCase().trim();

    try {
      if (wktUpper.startsWith('POINT')) {
        return this.parsePoint(wkt, record, rowId);
      } else if (wktUpper.startsWith('LINESTRING')) {
        return this.parseLineString(wkt, record, rowId);
      } else if (wktUpper.startsWith('POLYGON')) {
        return this.parsePolygon(wkt, record, rowId);
      } else if (wktUpper.startsWith('MULTIPOINT')) {
        return this.parseMultiPoint(wkt, record, rowId);
      } else {
        console.warn(`Type de géométrie WKT non supporté: ${wktUpper.split('(')[0]}`);
        return null;
      }
    } catch (error) {
      console.error(`Erreur parsing WKT "${wkt}":`, error);
      return null;
    }
  }

  /**
   * Parse un POINT WKT vers un Marker Leaflet
   */
  private parsePoint(wkt: string, record: any, rowId: number): L.Marker {
    // Extraire les coordonnées : POINT(lon lat) ou POINT (lon lat)
    const match = wkt.match(/POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/i);
    if (!match) {
      throw new Error(`Format POINT invalide: ${wkt}`);
    }

    const lon = parseFloat(match[1]);
    const lat = parseFloat(match[2]);

    if (isNaN(lon) || isNaN(lat)) {
      throw new Error(`Coordonnées invalides dans POINT: ${wkt}`);
    }

    // Créer le marker avec popup
    const marker = L.marker([lat, lon], {
      icon: this.createCustomIcon('point')
    });

    // Ajouter popup avec informations du record
    const popupContent = this.createPopupContent(record);
    marker.bindPopup(popupContent);

    // Gérer la sélection
    marker.on('click', () => {
      this.selectRecord(rowId);
    });

    return marker;
  }

  /**
   * Parse un LINESTRING WKT vers une Polyline Leaflet  
   */
  private parseLineString(wkt: string, record: any, rowId: number): L.Polyline {
    // Extraire les points : LINESTRING(lon1 lat1, lon2 lat2, ...)
    const match = wkt.match(/LINESTRING\s*\(\s*(.+)\s*\)/i);
    if (!match) {
      throw new Error(`Format LINESTRING invalide: ${wkt}`);
    }

    const coordsStr = match[1];
    const points: L.LatLng[] = [];

    // Parser chaque paire de coordonnées
    const coordPairs = coordsStr.split(',');
    for (const pair of coordPairs) {
      const coords = pair.trim().split(/\s+/);
      if (coords.length >= 2) {
        const lon = parseFloat(coords[0]);
        const lat = parseFloat(coords[1]);
        if (!isNaN(lon) && !isNaN(lat)) {
          points.push(L.latLng(lat, lon));
        }
      }
    }

    if (points.length < 2) {
      throw new Error(`LINESTRING doit avoir au moins 2 points: ${wkt}`);
    }

    // Créer la polyline
    const polyline = L.polyline(points, {
      color: '#3388ff',
      weight: 3,
      opacity: 0.7
    });

    // Ajouter popup
    polyline.bindPopup(this.createPopupContent(record));
    polyline.on('click', () => this.selectRecord(rowId));

    return polyline;
  }

  /**
   * Parse un POLYGON WKT vers un Polygon Leaflet
   */
  private parsePolygon(wkt: string, record: any, rowId: number): L.Polygon {
    // Extraire l'anneau extérieur : POLYGON((lon1 lat1, lon2 lat2, ...))
    const match = wkt.match(/POLYGON\s*\(\s*\((.+?)\)\s*\)/i);
    if (!match) {
      throw new Error(`Format POLYGON invalide: ${wkt}`);
    }

    const coordsStr = match[1];
    const points: L.LatLng[] = [];

    // Parser les coordonnées de l'anneau extérieur
    const coordPairs = coordsStr.split(',');
    for (const pair of coordPairs) {
      const coords = pair.trim().split(/\s+/);
      if (coords.length >= 2) {
        const lon = parseFloat(coords[0]);
        const lat = parseFloat(coords[1]);
        if (!isNaN(lon) && !isNaN(lat)) {
          points.push(L.latLng(lat, lon));
        }
      }
    }

    if (points.length < 3) {
      throw new Error(`POLYGON doit avoir au moins 3 points: ${wkt}`);
    }

    // Créer le polygone
    const polygon = L.polygon(points, {
      color: '#ff7800',
      fillColor: '#ff7800',
      fillOpacity: 0.2,
      weight: 2
    });

    // Ajouter popup
    polygon.bindPopup(this.createPopupContent(record));
    polygon.on('click', () => this.selectRecord(rowId));

    return polygon;
  }

  /**
   * Parse un MULTIPOINT WKT vers plusieurs Markers
   */
  private parseMultiPoint(wkt: string, record: any, rowId: number): L.LayerGroup {
    // Extraire les points : MULTIPOINT((lon1 lat1), (lon2 lat2), ...)
    const pointMatches = wkt.match(/\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/gi);
    if (!pointMatches || pointMatches.length === 0) {
      throw new Error(`Format MULTIPOINT invalide: ${wkt}`);
    }

    const layerGroup = L.layerGroup();

    pointMatches.forEach((pointStr, index) => {
      try {
        const fakeWkt = `POINT${pointStr}`;
        const marker = this.parsePoint(fakeWkt, record, rowId);
        layerGroup.addLayer(marker);
      } catch (error) {
        console.warn(`Erreur parsing point ${index} dans MULTIPOINT:`, error);
      }
    });

    return layerGroup;
  }

  /**
   * Crée le contenu HTML pour le popup d'un record
   */
  private createPopupContent(record: any): string {
    const fields = this.field.viewSection().viewFields().peek();
    let content = '<div class="map-popup">';
    
    // Afficher les premiers champs significatifs
    fields.slice(0, 5).forEach(field => {
      const fieldName = field.label();
      const fieldValue = record[field.colId()];
      
      if (fieldValue && fieldValue !== '' && fieldName !== this.field.label()) {
        content += `<div class="popup-field">
          <strong>${fieldName}:</strong> ${this.formatFieldValue(fieldValue)}
        </div>`;
      }
    });
    
    content += '</div>';
    return content;
  }

  /**
   * Formate une valeur de champ pour l'affichage dans le popup
   */
  private formatFieldValue(value: any): string {
    if (value === null || value === undefined) return '';
    if (typeof value === 'string' && value.length > 100) {
      return value.substring(0, 100) + '...';
    }
    return String(value);
  }

  /**
   * Crée une icône personnalisée pour les markers
   */
  private createCustomIcon(type: string): L.Icon {
    const iconOptions: L.IconOptions = {
      iconSize: [25, 25],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    };

    switch (type) {
      case 'point':
        return L.icon({
          ...iconOptions,
          iconUrl: 'data:image/svg+xml;base64,' + btoa(`
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#3388ff">
              <circle cx="12" cy="12" r="8"/>
              <circle cx="12" cy="12" r="4" fill="white"/>
            </svg>
          `)
        });
      default:
        return L.icon(iconOptions);
    }
  }

  /**
   * Sélectionne un record dans Grist
   */
  private selectRecord(rowId: number): void {
    const viewInstance = this.field.viewSection().viewInstance();
    const cursor = viewInstance.cursor;
    
    // Trouver l'index du record
    const allRecords = viewInstance.viewData.peek();
    let targetIndex = -1;
    
    allRecords.some((record: any, index: number) => {
      if (record.id() === rowId) {
        targetIndex = index;
        return true;
      }
      return false;
    });

    if (targetIndex >= 0) {
      cursor.setCursorPos(targetIndex);
    }
  }

  /**
   * Met à jour la sélection sur la carte
   */
  private updateSelection(): void {
    // TODO: Mettre en surbrillance le marker/geometry sélectionné
    // Cette fonctionnalité nécessite de maintenir une référence aux layers
  }

  /**
   * Ajuste la vue de la carte pour inclure toutes les géométries
   */
  private fitBounds(): void {
    if (!this.map || !this.geometryLayer) return;

    const group = L.featureGroup([this.geometryLayer]);
    if (this.clusterGroup) {
      group.addLayer(this.clusterGroup);
    }

    if (group.getLayers().length > 0) {
      this.map.fitBounds(group.getBounds(), { padding: [10, 10] });
    }
  }

  /**
   * Active/Désactive le clustering des points
   */
  private toggleClustering(): void {
    // TODO: Implémenter le toggle clustering
    console.log('Toggle clustering - à implémenter');
  }

  /**
   * Active/Désactive le mode heatmap
   */
  private toggleHeatmap(): void {
    // TODO: Implémenter la heatmap
    console.log('Toggle heatmap - à implémenter');
  }

  /**
   * Ouvre l'éditeur de styles de carte
   */
  private openStyleEditor(): void {
    // TODO: Implémenter l'éditeur de styles
    console.log('Éditeur de styles - à implémenter');
  }

  /**
   * Nettoie les ressources de la carte
   */
  private disposeMap(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
    this.geometryLayer = null;
    this.clusterGroup = null;
    this.mapContainer = null;
  }
}

const MapContainer = styled('div', `
  .map-widget {
    border: 1px solid #ddd;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .map-controls {
    display: flex;
    gap: 8px;
    padding: 8px;
    background: #f8f9fa;
    border-top: 1px solid #ddd;
  }
  
  .map-btn {
    padding: 4px 8px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background: white;
    cursor: pointer;
    font-size: 12px;
  }
  
  .map-btn:hover {
    background: #e9ecef;
  }
  
  .map-popup {
    font-size: 13px;
    max-width: 200px;
  }
  
  .popup-field {
    margin-bottom: 4px;
  }
  
  .popup-field strong {
    color: #555;
  }
`);
