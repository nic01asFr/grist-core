import {DataRowModel} from 'app/client/models/DataRowModel';
import {ViewFieldRec} from 'app/client/models/entities/ViewFieldRec';
import {KoSaveableObservable} from 'app/client/models/modelUtil';
import {NewBaseEditor, Options} from 'app/client/widgets/NewBaseEditor';
import {undef} from 'app/common/gutil';
import {dom, DomContents, Observable} from 'grainjs';
import * as ko from 'knockout';

/**
 * VectorEditor - A basic editor for vector embeddings/arrays.
 * 
 * This editor allows users to:
 * - View vectors as JSON arrays
 * - Edit vectors as comma-separated values or JSON arrays
 * - Basic validation for numeric arrays
 * 
 * Future enhancements could include:
 * - Visual representation of vectors
 * - Vector similarity calculations
 * - Integration with ML/AI services for embedding generation
 */
export class VectorEditor extends NewBaseEditor {
  private _textObs: Observable<string>;
  private _dimensions: number | null = null;

  constructor(options: Options) {
    super(options);
    
    // Try to parse dimensions from column type (e.g., "Vector:512")
    const colType = this.field.column().type();
    const match = colType.match(/Vector:(\d+)/);
    if (match) {
      this._dimensions = parseInt(match[1], 10);
    }
    
    const cellValue = this.getCellValue();
    let displayValue = '';
    if (cellValue && Array.isArray(cellValue)) {
      displayValue = JSON.stringify(cellValue);
    } else if (cellValue) {
      displayValue = String(cellValue);
    }
    
    this._textObs = Observable.create(this, displayValue);
    
    // Update the cell when the text changes
    this._textObs.addListener((value) => {
      if (this.isDisposed()) { return; }
      const parsedVector = this.parseVector(value);
      this.setValue(parsedVector);
    });
  }

  public attach(cellElem: Element): void {
    // Create the text input element
    const textInput = dom('textarea',
      {
        class: 'celleditor_text_editor',
        style: 'min-height: 60px; font-family: monospace;',
        placeholder: this._dimensions ? 
          `Enter ${this._dimensions}-dimensional vector (e.g. [1,2,3] or 1,2,3)` :
          'Enter vector as array (e.g. [1,2,3] or 1,2,3)',
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
        class: 'vector-helper',
        style: `
          font-size: 11px;
          color: #666;
          margin-top: 4px;
          padding: 4px;
          background: #f9f9f9;
          border-radius: 3px;
        `
      },
      this._dimensions ?
        `Expected dimensions: ${this._dimensions}. Format: [1.0,2.0,3.0] or 1.0,2.0,3.0` :
        'Format: [1.0,2.0,3.0] or 1.0,2.0,3.0'
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
    
    if (value) {
      const parsedVector = this.parseVector(value);
      if (!parsedVector) {
        this.showValidationError('Invalid vector format. Please use [1,2,3] or 1,2,3 format.');
        return;
      }
      
      if (this._dimensions && parsedVector.length !== this._dimensions) {
        this.showValidationError(`Vector dimension mismatch: expected ${this._dimensions}, got ${parsedVector.length}`);
        return;
      }
    }
    
    const finalValue = value ? this.parseVector(value) : null;
    this.setValue(finalValue);
    this.save(this.getCellValue());
  }

  private parseVector(input: string): number[] | null {
    if (!input.trim()) return null;
    
    try {
      // Try parsing as JSON array first
      if (input.trim().startsWith('[') && input.trim().endsWith(']')) {
        const parsed = JSON.parse(input);
        if (Array.isArray(parsed) && parsed.every(x => typeof x === 'number' || !isNaN(Number(x)))) {
          return parsed.map(x => Number(x));
        }
      }
      
      // Try parsing as comma-separated values
      const values = input.split(',').map(v => v.trim());
      if (values.every(v => v && !isNaN(Number(v)))) {
        return values.map(v => Number(v));
      }
      
      return null;
    } catch (e) {
      return null;
    }
  }

  private showValidationError(message: string): void {
    // TODO: Implement proper error display
    // For now, just use console.warn
    console.warn('Vector validation error:', message);
  }

  private cancelEdit(): void {
    const cellValue = this.getCellValue();
    let displayValue = '';
    if (cellValue && Array.isArray(cellValue)) {
      displayValue = JSON.stringify(cellValue);
    } else if (cellValue) {
      displayValue = String(cellValue);
    }
    this._textObs.set(displayValue);
    this.save(this.getCellValue());
  }
}

/**
 * VectorTextBox - Display widget for vector data
 */
export class VectorTextBox extends NewBaseEditor {
  
  public buildDom(): DomContents {
    const value = this.getCellValue();
    let displayValue = '';
    let tooltipValue = '';
    
    if (value && Array.isArray(value)) {
      tooltipValue = `Vector (${value.length}D): [${value.join(', ')}]`;
      
      // Show compact representation
      if (value.length <= 5) {
        displayValue = `[${value.map(x => Number(x).toFixed(3)).join(', ')}]`;
      } else {
        displayValue = `[${value.slice(0, 3).map(x => Number(x).toFixed(3)).join(', ')}, ... +${value.length - 3} more]`;
      }
    }
    
    return dom('div.field_clip',
      {
        style: 'font-family: monospace; font-size: 11px; color: #2196F3;'
      },
      displayValue || dom('span.empty_cell', 'empty'),
      tooltipValue ? {title: tooltipValue} : {}
    );
  }
}
