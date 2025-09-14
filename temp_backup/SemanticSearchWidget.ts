import {GristDoc} from 'app/client/components/GristDoc';
import {makeT} from 'app/client/lib/localization';
import {AppModel} from 'app/client/models/AppModel';
import {reportError} from 'app/client/models/errors';
import {ViewSectionRec} from 'app/client/models/entities/ViewSectionRec';
import {basicButton, primaryButton} from 'app/client/ui2018/buttons';
import {icon} from 'app/client/ui2018/icons';
import {loadingSpinner} from 'app/client/ui2018/loaders';
import {menu, menuItem} from 'app/client/ui2018/menus';
import {confirmModal} from 'app/client/ui2018/modals';
import {Computed, Disposable, dom, DomElementArg, makeTestId, Observable, styled} from 'grainjs';

const t = makeT('SemanticSearchWidget');
const testId = makeTestId('test-semantic-search-');

/**
 * Interface de recherche sémantique pour Grist
 * 
 * Fonctionnalités :
 * - Recherche en langage naturel dans toutes les données
 * - Affichage des résultats avec score de similarité
 * - Navigation vers les enregistrements trouvés
 * - Filtrage par tables et champs
 * - Historique des recherches
 * - Suggestions de recherche
 * - Mode clustering pour explorer les données
 */

export interface SemanticSearchResult {
  table: string;
  rowId: number;
  similarity: number;
  content: string;
  fields: Record<string, any>;
  tableName?: string;
}

export interface SearchOptions {
  query: string;
  limit: number;
  threshold: number;
  tables?: string[];
  includeContent: boolean;
}

export class SemanticSearchWidget extends Disposable {
  private _searchQuery = Observable.create(this, '');
  private _isSearching = Observable.create(this, false);
  private _searchResults = Observable.create<SemanticSearchResult[]>(this, []);
  private _searchOptions = Observable.create<SearchOptions>(this, {
    query: '',
    limit: 20,
    threshold: 0.3,
    includeContent: true
  });
  private _searchHistory = Observable.create<string[]>(this, []);
  private _selectedTable = Observable.create<string>(this, '');
  private _showAdvanced = Observable.create<boolean>(this, false);

  constructor(
    private _gristDoc: GristDoc,
    private _appModel: AppModel
  ) {
    super();
    
    // Charger l'historique des recherches depuis le localStorage
    this._loadSearchHistory();
    
    // Auto-complete après 500ms de pause
    this.autoDispose(this._searchQuery.addListener(
      (query) => this._debouncedSearch(query)
    ));
  }

  public buildDom(): DomElementArg {
    return SemanticSearchContainer(
      testId('container'),
      
      // En-tête avec titre et options
      dom('div.search-header',
        dom('h3.search-title', 
          icon('Search'), 
          t('Recherche Sémantique')
        ),
        dom('div.search-actions',
          basicButton(icon('Settings'), 
            dom.on('click', () => this._showAdvanced.set(!this._showAdvanced.get())),
            testId('settings-btn')
          ),
          basicButton(icon('History'), 
            dom.on('click', (ev) => this._showHistoryMenu(ev)),
            testId('history-btn')
          )
        )
      ),

      // Barre de recherche principale
      dom('div.search-bar',
        dom('input.search-input',
          dom.prop('value', this._searchQuery),
          dom.on('input', (ev, elem) => this._searchQuery.set(elem.value)),
          dom.on('keydown', (ev) => {
            if (ev.key === 'Enter') {
              this._performSearch();
            }
          }),
          attr.placeholder(t('Rechercher dans vos données... (ex: "clients parisiens", "projets urgents")')),
          testId('search-input')
        ),
        primaryButton(
          dom.text(() => this._isSearching.get() ? '' : t('Rechercher')),
          dom.maybe(this._isSearching, () => loadingSpinner()),
          dom.on('click', () => this._performSearch()),
          dom.prop('disabled', this._isSearching),
          testId('search-btn')
        )
      ),

      // Options avancées (repliables)
      dom.maybe(this._showAdvanced, () => 
        dom('div.search-advanced',
          dom('div.advanced-row',
            dom('label', t('Nombre de résultats:')),
            dom('input.number-input',
              dom.prop('type', 'number'),
              dom.prop('min', '1'),
              dom.prop('max', '100'),
              dom.prop('value', () => String(this._searchOptions.get().limit)),
              dom.on('input', (ev, elem) => {
                const opts = this._searchOptions.get();
                this._searchOptions.set({...opts, limit: parseInt(elem.value) || 20});
              })
            )
          ),
          dom('div.advanced-row',
            dom('label', t('Seuil de similarité:')),
            dom('input.range-input',
              dom.prop('type', 'range'),
              dom.prop('min', '0'),
              dom.prop('max', '1'),
              dom.prop('step', '0.1'),
              dom.prop('value', () => String(this._searchOptions.get().threshold)),
              dom.on('input', (ev, elem) => {
                const opts = this._searchOptions.get();
                this._searchOptions.set({...opts, threshold: parseFloat(elem.value)});
              })
            ),
            dom('span.threshold-value', 
              dom.text(() => `${Math.round(this._searchOptions.get().threshold * 100)}%`)
            )
          ),
          dom('div.advanced-row',
            dom('label', t('Table spécifique:')),
            dom('select.table-select',
              dom.prop('value', this._selectedTable),
              dom.on('change', (ev, elem) => this._selectedTable.set(elem.value)),
              dom('option', {value: ''}, t('Toutes les tables')),
              ...this._getTableOptions()
            )
          )
        )
      ),

      // Zone de suggestions rapides
      dom('div.search-suggestions',
        dom('div.suggestions-header', t('Suggestions:')),
        dom('div.suggestions-list',
          this._buildSuggestions()
        )
      ),

      // Résultats de recherche
      dom('div.search-results',
        dom.domComputed(this._searchResults, (results) => 
          results.length === 0 
            ? this._buildEmptyState()
            : this._buildResultsList(results)
        )
      ),

      // Actions en bas
      dom('div.search-footer',
        dom.maybe(() => this._searchResults.get().length > 0, () =>
          dom('div.results-actions',
            basicButton(t('Exporter les résultats'), 
              dom.on('click', () => this._exportResults()),
              testId('export-btn')
            ),
            basicButton(t('Créer une vue filtré'), 
              dom.on('click', () => this._createFilteredView()),
              testId('create-view-btn')
            ),
            basicButton(t('Analyser les clusters'), 
              dom.on('click', () => this._showClusters()),
              testId('clusters-btn')
            )
          )
        )
      )
    );
  }

  /**
   * Construit les suggestions de recherche
   */
  private _buildSuggestions(): DomElementArg[] {
    const suggestions = [
      { icon: 'Users', text: 'clients actifs', query: 'clients actifs récents' },
      { icon: 'MapPin', text: 'lieux Paris', query: 'adresses Paris centre' },
      { icon: 'Calendar', text: 'cette semaine', query: 'événements cette semaine' },
      { icon: 'Star', text: 'top qualité', query: 'meilleure qualité évaluation' },
      { icon: 'TrendingUp', text: 'croissance', query: 'croissance progression augmentation' }
    ];

    return suggestions.map(suggestion =>
      dom('button.suggestion-btn',
        icon(suggestion.icon),
        dom.text(suggestion.text),
        dom.on('click', () => {
          this._searchQuery.set(suggestion.query);
          this._performSearch();
        }),
        testId(`suggestion-${suggestion.text}`)
      )
    );
  }

  /**
   * Construit l'état vide (pas de résultats)
   */
  private _buildEmptyState(): DomElementArg {
    const hasSearched = this._searchQuery.get().trim().length > 0;
    
    return dom('div.empty-state',
      icon(hasSearched ? 'Search' : 'Lightbulb'),
      dom('h4', hasSearched ? t('Aucun résultat trouvé') : t('Recherchez dans vos données')),
      dom('p', 
        hasSearched 
          ? t('Essayez avec des termes différents ou réduisez le seuil de similarité')
          : t('Utilisez la recherche sémantique pour trouver des informations par sens, pas seulement par mots-clés exacts')
      ),
      !hasSearched ? dom('div.example-searches',
        dom('p.examples-title', t('Exemples de recherches:')),
        dom('ul',
          dom('li', '"projets en retard"'),
          dom('li', '"clients satisfaits"'),
          dom('li', '"documents importants"'),
          dom('li', '"événements à venir"')
        )
      ) : null
    );
  }

  /**
   * Construit la liste des résultats
   */
  private _buildResultsList(results: SemanticSearchResult[]): DomElementArg {
    return dom('div.results-list',
      dom('div.results-header',
        dom('h4', t(`{{count}} résultats trouvés`, { count: results.length })),
        dom('div.results-sort',
          dom('label', t('Trier par:')),
          dom('select',
            dom('option', {value: 'similarity'}, t('Pertinence')),
            dom('option', {value: 'table'}, t('Table')),
            dom('option', {value: 'recent'}, t('Plus récent'))
          )
        )
      ),
      ...results.map((result, index) => this._buildResultItem(result, index))
    );
  }

  /**
   * Construit un élément de résultat
   */
  private _buildResultItem(result: SemanticSearchResult, index: number): DomElementArg {
    const similarityPercent = Math.round(result.similarity * 100);
    const isHighRelevance = result.similarity > 0.7;
    
    return dom('div.result-item',
      dom.cls('high-relevance', isHighRelevance),
      
      // Score de similarité
      dom('div.result-score',
        dom('div.score-circle', 
          dom.cls('high-score', isHighRelevance),
          dom.text(`${similarityPercent}%`)
        )
      ),

      // Contenu principal
      dom('div.result-content',
        // En-tête avec table et actions
        dom('div.result-header',
          dom('span.result-table', 
            icon('Table'), 
            dom.text(result.tableName || result.table)
          ),
          dom('div.result-actions',
            basicButton(icon('Eye'), t('Voir'),
              dom.on('click', () => this._navigateToResult(result)),
              testId(`view-result-${index}`)
            ),
            basicButton(icon('Edit'), t('Éditer'),
              dom.on('click', () => this._editResult(result)),
              testId(`edit-result-${index}`)
            )
          )
        ),

        // Contenu du résultat
        dom('div.result-text', 
          dom.text(this._truncateText(result.content, 200))
        ),

        // Champs pertinents
        dom('div.result-fields',
          ...this._buildFieldsPreview(result.fields)
        )
      )
    );
  }

  /**
   * Construit l'aperçu des champs d'un résultat
   */
  private _buildFieldsPreview(fields: Record<string, any>): DomElementArg[] {
    const importantFields = Object.entries(fields)
      .filter(([key, value]) => value && typeof value === 'string' && value.length > 0)
      .slice(0, 3); // Limiter à 3 champs

    return importantFields.map(([key, value]) =>
      dom('div.result-field',
        dom('span.field-name', `${key}:`),
        dom('span.field-value', this._truncateText(String(value), 100))
      )
    );
  }

  /**
   * Recherche avec debouncing
   */
  private _debounceTimer: any = null;
  private _debouncedSearch(query: string): void {
    if (this._debounceTimer) {
      clearTimeout(this._debounceTimer);
    }
    
    this._debounceTimer = setTimeout(() => {
      if (query.trim().length >= 3) {
        this._performSearch();
      }
    }, 500);
  }

  /**
   * Effectue la recherche sémantique
   */
  private async _performSearch(): Promise<void> {
    const query = this._searchQuery.get().trim();
    if (!query) return;

    this._isSearching.set(true);
    
    try {
      const options = {
        ...this._searchOptions.get(),
        query,
        tables: this._selectedTable.get() ? [this._selectedTable.get()] : undefined
      };

      // Appel API
      const response = await this._gristDoc.docApi.request('semantic-search', {
        method: 'POST',
        body: JSON.stringify(options)
      });

      const results: SemanticSearchResult[] = response.results || [];
      
      // Enrichir les résultats avec les noms de tables
      const enrichedResults = await Promise.all(
        results.map(async (result) => {
          try {
            const tableName = await this._getTableDisplayName(result.table);
            return { ...result, tableName };
          } catch (error) {
            return result;
          }
        })
      );

      this._searchResults.set(enrichedResults);
      
      // Ajouter à l'historique
      this._addToHistory(query);

    } catch (error) {
      console.error('Erreur recherche sémantique:', error);
      reportError(error);
    } finally {
      this._isSearching.set(false);
    }
  }

  /**
   * Navigation vers un résultat
   */
  private async _navigateToResult(result: SemanticSearchResult): Promise<void> {
    try {
      // Ouvrir la table et sélectionner la ligne
      const viewId = await this._gristDoc.openDocPage(result.table);
      if (viewId) {
        // Sélectionner la ligne spécifique
        await this._gristDoc.moveToCursorPos(result.rowId);
      }
    } catch (error) {
      console.error('Erreur navigation vers résultat:', error);
      reportError(error);
    }
  }

  /**
   * Édition d'un résultat
   */
  private async _editResult(result: SemanticSearchResult): Promise<void> {
    // Similaire à navigateToResult mais ouvre en mode édition
    await this._navigateToResult(result);
    // TODO: Activer le mode édition sur la ligne
  }

  /**
   * Obtenir le nom d'affichage d'une table
   */
  private async _getTableDisplayName(tableId: string): Promise<string> {
    try {
      const tables = await this._gristDoc.getDocStructure();
      const table = tables.tables?.find(t => t.id === tableId);
      return table?.name || tableId;
    } catch (error) {
      return tableId;
    }
  }

  /**
   * Obtenir les options de tables pour le sélecteur
   */
  private _getTableOptions(): DomElementArg[] {
    // Cette méthode devrait être reactive et obtenir les vraies tables du doc
    // Pour la démo, retourner quelques options statiques
    const tables = [
      { id: 'Clients', name: 'Clients' },
      { id: 'Projets', name: 'Projets' },
      { id: 'Documents', name: 'Documents' },
      { id: 'Événements', name: 'Événements' }
    ];

    return tables.map(table =>
      dom('option', { value: table.id }, table.name)
    );
  }

  /**
   * Afficher le menu historique
   */
  private _showHistoryMenu(ev: MouseEvent): void {
    const history = this._searchHistory.get();
    if (history.length === 0) return;

    menu(ev.target as Element,
      history.map(query =>
        menuItem(() => {
          this._searchQuery.set(query);
          this._performSearch();
        }, query)
      ),
      { placement: 'bottom-start' }
    );
  }

  /**
   * Ajouter à l'historique des recherches
   */
  private _addToHistory(query: string): void {
    const history = this._searchHistory.get();
    const filtered = history.filter(q => q !== query);
    const newHistory = [query, ...filtered].slice(0, 10); // Garder 10 dernières
    this._searchHistory.set(newHistory);
    this._saveSearchHistory(newHistory);
  }

  /**
   * Charger l'historique depuis localStorage
   */
  private _loadSearchHistory(): void {
    try {
      const stored = localStorage.getItem('grist-semantic-search-history');
      if (stored) {
        const history = JSON.parse(stored);
        if (Array.isArray(history)) {
          this._searchHistory.set(history);
        }
      }
    } catch (error) {
      console.warn('Erreur chargement historique recherche:', error);
    }
  }

  /**
   * Sauvegarder l'historique dans localStorage
   */
  private _saveSearchHistory(history: string[]): void {
    try {
      localStorage.setItem('grist-semantic-search-history', JSON.stringify(history));
    } catch (error) {
      console.warn('Erreur sauvegarde historique recherche:', error);
    }
  }

  /**
   * Tronquer le texte avec ellipses
   */
  private _truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }

  /**
   * Exporter les résultats
   */
  private _exportResults(): void {
    // TODO: Implémenter l'export CSV/JSON des résultats
    console.log('Export results - à implémenter');
  }

  /**
   * Créer une vue filtrée basée sur les résultats
   */
  private _createFilteredView(): void {
    // TODO: Créer une nouvelle vue Grist avec les résultats
    console.log('Create filtered view - à implémenter');
  }

  /**
   * Afficher l'analyse des clusters
   */
  private _showClusters(): void {
    // TODO: Ouvrir un modal avec l'analyse des clusters sémantiques
    console.log('Show clusters - à implémenter');
  }
}

const SemanticSearchContainer = styled('div', `
  .search-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid #ddd;
  }
  
  .search-title {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #333;
  }
  
  .search-actions {
    display: flex;
    gap: 8px;
  }
  
  .search-bar {
    display: flex;
    gap: 12px;
    padding: 16px;
    align-items: center;
  }
  
  .search-input {
    flex: 1;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
  }
  
  .search-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }
  
  .search-advanced {
    background: #f8f9fa;
    padding: 16px;
    border-top: 1px solid #ddd;
  }
  
  .advanced-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }
  
  .advanced-row label {
    min-width: 140px;
    font-weight: 500;
  }
  
  .number-input, .range-input, .table-select {
    padding: 6px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .threshold-value {
    font-weight: 500;
    color: #007bff;
  }
  
  .search-suggestions {
    padding: 16px;
    border-top: 1px solid #eee;
  }
  
  .suggestions-header {
    font-weight: 500;
    margin-bottom: 8px;
    color: #666;
  }
  
  .suggestions-list {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .suggestion-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border: 1px solid #ddd;
    border-radius: 20px;
    background: white;
    color: #555;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .suggestion-btn:hover {
    background: #f0f0f0;
    border-color: #007bff;
    color: #007bff;
  }
  
  .search-results {
    flex: 1;
    overflow-y: auto;
  }
  
  .empty-state {
    text-align: center;
    padding: 48px 24px;
    color: #666;
  }
  
  .empty-state h4 {
    margin: 16px 0 8px 0;
    color: #333;
  }
  
  .example-searches {
    margin-top: 24px;
    text-align: left;
    max-width: 300px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .examples-title {
    font-weight: 500;
    color: #333;
  }
  
  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid #eee;
  }
  
  .results-sort {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .result-item {
    display: flex;
    padding: 16px;
    border-bottom: 1px solid #eee;
    transition: background-color 0.2s;
  }
  
  .result-item:hover {
    background-color: #f8f9fa;
  }
  
  .result-item.high-relevance {
    border-left: 3px solid #28a745;
  }
  
  .result-score {
    flex-shrink: 0;
    margin-right: 16px;
  }
  
  .score-circle {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: #f0f0f0;
    color: #666;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
    font-size: 12px;
  }
  
  .score-circle.high-score {
    background: #d4edda;
    color: #155724;
  }
  
  .result-content {
    flex: 1;
  }
  
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .result-table {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
    color: #007bff;
  }
  
  .result-actions {
    display: flex;
    gap: 8px;
  }
  
  .result-text {
    margin-bottom: 12px;
    line-height: 1.4;
    color: #333;
  }
  
  .result-fields {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .result-field {
    display: flex;
    gap: 8px;
    font-size: 13px;
  }
  
  .field-name {
    font-weight: 500;
    color: #666;
    min-width: 80px;
  }
  
  .field-value {
    color: #333;
  }
  
  .search-footer {
    border-top: 1px solid #ddd;
    padding: 16px;
  }
  
  .results-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
  }
`);
