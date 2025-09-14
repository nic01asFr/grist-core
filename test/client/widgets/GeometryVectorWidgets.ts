import {assert} from 'chai';
import {Geometry, Vector} from 'sandbox/grist/usertypes';

/**
 * Tests unitaires pour les widgets Geometry et Vector
 * Ces tests valident le comportement des nouveaux types de données dans l'interface utilisateur
 */
describe('GeometryVectorWidgets', function() {

  describe('Geometry Type', function() {
    let geometryType: Geometry;

    beforeEach(function() {
      geometryType = new Geometry();
    });

    it('should have correct type name', function() {
      assert.equal(Geometry.typename(), 'Geometry');
    });

    it('should have null as default value', function() {
      assert.isNull(geometryType.default);
    });

    it('should validate WKT points correctly', function() {
      const validPoints = [
        'POINT(2.3 48.8)',
        'POINT(-0.1 51.5)',
        'POINT(0 0)',
        'point(2.3 48.8)', // case insensitive
      ];

      for (const point of validPoints) {
        assert.isTrue(Geometry.is_right_type(Geometry.do_convert(point)), 
                     `Point should be valid: ${point}`);
      }
    });

    it('should validate WKT polygons correctly', function() {
      const polygon = 'POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))';
      const result = Geometry.do_convert(polygon);
      assert.isTrue(Geometry.is_right_type(result));
      assert.equal(result, polygon);
    });

    it('should validate WKT linestrings correctly', function() {
      const linestring = 'LINESTRING(0 0, 1 1, 2 2)';
      const result = Geometry.do_convert(linestring);
      assert.isTrue(Geometry.is_right_type(result));
      assert.equal(result, linestring);
    });

    it('should convert GeoJSON points to WKT', function() {
      const geojsonPoint = {
        type: 'Point',
        coordinates: [2.3, 48.8]
      };
      
      const result = Geometry.do_convert(geojsonPoint);
      assert.equal(result, 'POINT(2.3 48.8)');
      assert.isTrue(Geometry.is_right_type(result));
    });

    it('should handle null and empty values', function() {
      assert.isNull(Geometry.do_convert(null));
      assert.isNull(Geometry.do_convert(''));
      assert.isNull(Geometry.do_convert('   '));
      
      assert.isTrue(Geometry.is_right_type(null));
    });

    it('should reject invalid WKT', function() {
      const invalidWKT = [
        'INVALID(1 2)',
        'POINT()',
        'POINT(a b)',
        '123',
        'random text'
      ];

      for (const wkt of invalidWKT) {
        assert.throws(() => Geometry.do_convert(wkt), 
                     /ConversionError/, 
                     `Should reject invalid WKT: ${wkt}`);
      }
    });

    it('should reject non-string types for is_right_type', function() {
      const invalidTypes = [123, 45.67, true, [], {}];
      
      for (const value of invalidTypes) {
        assert.isFalse(Geometry.is_right_type(value), 
                      `Should reject invalid type: ${typeof value}`);
      }
    });

    it('should validate internal WKT helper function', function() {
      // Valid WKT
      assert.isTrue(Geometry._is_valid_wkt('POINT(0 0)'));
      assert.isTrue(Geometry._is_valid_wkt('LINESTRING(0 0, 1 1)'));
      assert.isTrue(Geometry._is_valid_wkt('POLYGON((0 0, 1 0, 1 1, 0 0))'));
      
      // Invalid WKT  
      assert.isFalse(Geometry._is_valid_wkt('INVALID(0 0)'));
      assert.isFalse(Geometry._is_valid_wkt(''));
      assert.isFalse(Geometry._is_valid_wkt(null as any));
    });
  });

  describe('Vector Type', function() {
    let vectorType: Vector;

    beforeEach(function() {
      vectorType = new Vector();
    });

    it('should have correct type name', function() {
      assert.equal(Vector.typename(), 'Vector');
    });

    it('should have null as default value', function() {
      assert.isNull(vectorType.default);
    });

    it('should convert number arrays correctly', function() {
      const testVectors = [
        [1, 2, 3],
        [0.1, 0.2, 0.3],
        [1.0, -2.5, 3.14159],
        [-1, -2, -3],
        [0]
      ];

      for (const vector of testVectors) {
        const result = Vector.do_convert(vector);
        assert.isArray(result);
        assert.equal(result.length, vector.length);
        
        for (let i = 0; i < vector.length; i++) {
          assert.approximately(result[i], vector[i], 0.00001);
        }
        
        assert.isTrue(Vector.is_right_type(result));
      }
    });

    it('should convert tuples to arrays', function() {
      // Tuples in TypeScript/JavaScript are just arrays, but test the conversion
      const testTuple = [1, 2, 3];
      const result = Vector.do_convert(testTuple);
      
      assert.isArray(result);
      assert.deepEqual(result, [1.0, 2.0, 3.0]);
    });

    it('should parse JSON string vectors', function() {
      const jsonVectors = [
        '[1, 2, 3]',
        '[0.1, 0.2, 0.3]',
        '[-1.5, 2.5, -3.5]',
        '[42]',
        '  [1, 2, 3]  ' // with whitespace
      ];

      for (const jsonStr of jsonVectors) {
        const result = Vector.do_convert(jsonStr);
        const expected = JSON.parse(jsonStr.trim());
        
        assert.deepEqual(result, expected);
        assert.isTrue(Vector.is_right_type(result));
      }
    });

    it('should parse CSV string vectors', function() {
      const csvTests = [
        {input: '1,2,3', expected: [1, 2, 3]},
        {input: '0.1,0.2,0.3', expected: [0.1, 0.2, 0.3]},
        {input: '-1.5, 2.5, -3.5', expected: [-1.5, 2.5, -3.5]}, // with spaces
        {input: '42', expected: [42]},
        {input: '  1,  2,  3  ', expected: [1, 2, 3]} // extra spaces
      ];

      for (const {input, expected} of csvTests) {
        const result = Vector.do_convert(input);
        assert.deepEqual(result, expected, `Failed to parse CSV: ${input}`);
      }
    });

    it('should handle null and empty values', function() {
      assert.isNull(Vector.do_convert(null));
      assert.isNull(Vector.do_convert(''));
      assert.isNull(Vector.do_convert('   '));
      
      assert.isTrue(Vector.is_right_type(null));
    });

    it('should validate dimensions when specified', function() {
      const vectorWithDim = new Vector(3);
      
      // Valid dimension - should succeed
      const validResult = vectorWithDim.convert([1, 2, 3]);
      assert.deepEqual(validResult, [1.0, 2.0, 3.0]);
      
      // Invalid dimensions - should throw errors
      assert.throws(() => vectorWithDim.convert([1, 2]), /dimension/i);
      assert.throws(() => vectorWithDim.convert([1, 2, 3, 4]), /dimension/i);
    });

    it('should convert mixed type arrays', function() {
      const mixedTests = [
        {input: [1, 2.0, 3], expected: [1.0, 2.0, 3.0]},
        {input: ['1', '2', '3'], expected: [1.0, 2.0, 3.0]}, // string numbers
        {input: [1, '2.5', 3.0], expected: [1.0, 2.5, 3.0]} // mixed
      ];

      for (const {input, expected} of mixedTests) {
        const result = Vector.do_convert(input);
        assert.deepEqual(result, expected, `Failed mixed type conversion: ${JSON.stringify(input)}`);
      }
    });

    it('should reject invalid JSON strings', function() {
      const invalidJson = [
        '[1, 2, 3',  // missing bracket
        '1, 2, 3]',  // missing bracket
        '[1, 2, abc]',  // non-numeric
        'not json'
      ];

      for (const jsonStr of invalidJson) {
        assert.throws(() => Vector.do_convert(jsonStr), 
                     /ConversionError/, 
                     `Should reject invalid JSON: ${jsonStr}`);
      }
    });

    it('should reject invalid CSV strings', function() {
      const invalidCsv = [
        '1,2,abc',  // non-numeric value
        'a,b,c'     // all non-numeric
      ];

      for (const csvStr of invalidCsv) {
        assert.throws(() => Vector.do_convert(csvStr), 
                     /ConversionError/, 
                     `Should reject invalid CSV: ${csvStr}`);
      }
    });

    it('should reject completely invalid types', function() {
      const invalidTypes = [
        123,        // single number
        true,       // boolean
        {},         // empty object
        new Date()  // date object
      ];

      for (const value of invalidTypes) {
        assert.throws(() => Vector.do_convert(value), 
                     /ConversionError/, 
                     `Should reject invalid type: ${typeof value}`);
      }
    });

    it('should validate right types correctly', function() {
      // Valid types
      assert.isTrue(Vector.is_right_type(null));
      assert.isTrue(Vector.is_right_type([]));
      assert.isTrue(Vector.is_right_type([1, 2, 3]));
      assert.isTrue(Vector.is_right_type([0.1, 0.2, 0.3]));
      
      // Invalid types
      assert.isFalse(Vector.is_right_type(123));
      assert.isFalse(Vector.is_right_type('string'));
      assert.isFalse(Vector.is_right_type({}));
      assert.isFalse(Vector.is_right_type(true));
    });

    it('should handle large vectors efficiently', function() {
      // Test performance with OpenAI-sized vectors (1536 dimensions)
      const largeVector = Array.from({length: 1536}, (_, i) => i * 0.1);
      
      const start = Date.now();
      const result = Vector.do_convert(largeVector);
      const duration = Date.now() - start;
      
      assert.isArray(result);
      assert.equal(result.length, 1536);
      assert.isBelow(duration, 100, 'Large vector conversion should be fast (<100ms)');
      
      // Spot check some values
      assert.approximately(result[0], 0, 0.001);
      assert.approximately(result[10], 1.0, 0.001);
      assert.approximately(result[1535], 153.5, 0.001);
    });

    it('should handle edge cases properly', function() {
      // Test with infinity
      const infVector = [Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY, 0];
      const result = Vector.do_convert(infVector);
      
      assert.equal(result[0], Number.POSITIVE_INFINITY);
      assert.equal(result[1], Number.NEGATIVE_INFINITY);
      assert.equal(result[2], 0);
      
      // Test empty array
      const emptyResult = Vector.do_convert([]);
      assert.isArray(emptyResult);
      assert.equal(emptyResult.length, 0);
    });
  });

  describe('Type Integration', function() {
    it('should be properly registered in type system', function() {
      // Test that our types exist and can be instantiated
      const geometry = new Geometry();
      const vector = new Vector();
      
      assert.instanceOf(geometry, Geometry);
      assert.instanceOf(vector, Vector);
      
      // Test type names are correct
      assert.equal(Geometry.typename(), 'Geometry');
      assert.equal(Vector.typename(), 'Vector');
    });

    it('should have consistent default values', function() {
      const geometry = new Geometry();
      const vector = new Vector();
      
      assert.isNull(geometry.default);
      assert.isNull(vector.default);
    });

    it('should handle conversion errors gracefully', function() {
      // Test that invalid inputs throw appropriate errors
      assert.throws(() => Geometry.do_convert(123), /ConversionError/);
      assert.throws(() => Vector.do_convert({}), /ConversionError/);
      
      // Test that error messages are helpful
      try {
        Geometry.do_convert('INVALID_WKT');
        assert.fail('Should have thrown ConversionError');
      } catch (error) {
        assert.include(error.message.toLowerCase(), 'conversion');
      }
    });
  });

  describe('Widget Integration', function() {
    // These tests would normally require DOM manipulation and widget setup
    // For now, we test the core type conversion logic that widgets depend on
    
    it('should provide data suitable for text input widgets', function() {
      // Geometry -> String representation for TextBox
      const point = Geometry.do_convert('POINT(2.3 48.8)');
      assert.isString(point);
      assert.match(point, /POINT\(\s*[\d.-]+\s+[\d.-]+\s*\)/);
      
      // Vector -> Array that can be JSON stringified
      const vector = Vector.do_convert([1, 2, 3]);
      assert.isArray(vector);
      const jsonStr = JSON.stringify(vector);
      assert.equal(jsonStr, '[1,2,3]');
    });

    it('should validate user input as widgets would', function() {
      // Simulate widget validation workflow
      const userInputs = [
        {type: 'Geometry', value: 'POINT(2.3 48.8)', valid: true},
        {type: 'Geometry', value: 'INVALID_GEOM', valid: false},
        {type: 'Vector', value: '[1,2,3]', valid: true},
        {type: 'Vector', value: '1,2,3', valid: true},
        {type: 'Vector', value: 'invalid', valid: false}
      ];
      
      for (const {type, value, valid} of userInputs) {
        try {
          if (type === 'Geometry') {
            const result = Geometry.do_convert(value);
            assert.isTrue(valid, `${value} should be valid for Geometry`);
            assert.isNotNull(result);
          } else if (type === 'Vector') {
            const result = Vector.do_convert(value);
            assert.isTrue(valid, `${value} should be valid for Vector`);
            assert.isNotNull(result);
          }
        } catch (error) {
          assert.isFalse(valid, `${value} should be invalid for ${type}: ${error.message}`);
        }
      }
    });
  });
});
