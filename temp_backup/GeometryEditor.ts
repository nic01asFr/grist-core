import {DataRowModel} from 'app/client/models/DataRowModel';
import {ViewFieldRec} from 'app/client/models/entities/ViewFieldRec';
import {KoSaveableObservable} from 'app/client/models/modelUtil';
import {NewBaseEditor, Options} from 'app/client/widgets/NewBaseEditor';
import {undef} from 'app/common/gutil';
import {dom, DomContents, Observable} from 'grainjs';
import * as ko from 'knockout';

/**
 * GeometryEditor - A basic editor for geometry/spatial data.
 * 
 * This editor allows users to:
 * - View geometry data as WKT (Well-Known Text) strings
 * - Edit geometry data as WKT strings
 * - Basic validation for common WKT formats
 * 
 * Future enhancements could include:
 * - Interactive map widget for visual editing
 * - Support for different coordinate systems
 * - Import from GeoJSON, Shapefile, etc.
 */
export class GeometryEditor extends NewBaseEditor {
  private _textObs: Observable<string>;

  constructor(options: Options) {
    super(options);
    
    this._textObs = Observable.create(this, String(this.getCellValue() || ''));
    
    // Update the cell when the text changes
    this._textObs.addListener((value) => {
      if (this.isDisposed()) { return; }
      this.setValue(value || null);
    });
  }

  public attach(cellElem: Element): void {
    // Create the text input element
    const textInput = dom('textarea',
      {
        class: 'celleditor_text_editor',
        style: 'min-height: 60px; font-family: monospace;',
        placeholder: 'Enter WKT geometry (e.g. POINT(0 0))',
      },
      dom.prop('value', this._textObs),
      dom.on('input', (e, elem) => {
        this._textObs.set(elem.value);
      }),
      dom.on('blur', () => {
        this.validateAndSave();
      }),
      dom.on('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.validateAndSave();
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          this.cancelEdit();
        }
      })
    );

    // Add some helper text
    const helperText = dom('div',
      {
        class: 'geometry-helper',
        style: `
          font-size: 11px;
          color: #666;
          margin-top: 4px;
          padding: 4px;
          background: #f9f9f9;
          border-radius: 3px;
        `
      },
      'Examples: POINT(1 2), LINESTRING(0 0,1 1,2 2), POLYGON((0 0,4 0,4 4,0 4,0 0))'
    );

    const container = dom('div',
      textInput,
      helperText
    );

    cellElem.appendChild(container);
    textInput.focus();
    textInput.select();
  }

  private validateAndSave(): void {
    const value = this._textObs.get().trim();
    
    if (value && !this.isValidWKT(value)) {
      // Show error but don't save
      this.showValidationError('Invalid WKT format. Please check your geometry syntax.');
      return;
    }
    
    this.setValue(value || null);
    this.save(this.getCellValue());
  }

  private isValidWKT(wkt: string): boolean {
    // Basic WKT validation - just check if it starts with known geometry types
    const upperWKT = wkt.trim().toUpperCase();
    const validTypes = [
      'POINT', 'LINESTRING', 'POLYGON', 
      'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 
      'GEOMETRYCOLLECTION'
    ];
    
    return validTypes.some(type => upperWKT.startsWith(type + '('));
  }

  private showValidationError(message: string): void {
    // TODO: Implement proper error display
    // For now, just use console.warn
    console.warn('Geometry validation error:', message);
  }

  private cancelEdit(): void {
    this._textObs.set(String(this.getCellValue() || ''));
    this.save(this.getCellValue());
  }
}

/**
 * GeometryTextBox - Display widget for geometry data
 */
export class GeometryTextBox extends NewBaseEditor {
  
  public buildDom(): DomContents {
    const value = this.getCellValue();
    const displayValue = value ? String(value) : '';
    
    // Show truncated version if too long
    let displayText = displayValue;
    if (displayText.length > 100) {
      displayText = displayText.substring(0, 100) + '...';
    }
    
    return dom('div.field_clip',
      {
        style: 'font-family: monospace; font-size: 11px; line-height: 1.3;'
      },
      displayText || dom('span.empty_cell', 'empty'),
      displayValue && displayText !== displayValue ? 
        {title: displayValue} : // Show full value in tooltip if truncated
        {}
    );
  }
}
