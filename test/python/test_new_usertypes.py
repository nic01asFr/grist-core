#!/usr/bin/env python3
"""
Tests unitaires pour les nouveaux types Geometry et Vector dans Grist.
Ces tests sont critiques pour la contribution upstream au projet Grist.

Teste la conformité aux standards existants et la robustesse des implémentations.
"""
import unittest
import json
from sandbox.grist import usertypes
from sandbox.grist.usertypes import Geometry, Vector
from objtypes import ConversionError, AltText


class TestGeometryType(unittest.TestCase):
    """Tests pour le type Geometry - données spatiales WKT"""
    
    def setUp(self):
        self.geometry_type = Geometry()
    
    def test_typename(self):
        """Test que le nom du type est correct"""
        self.assertEqual(Geometry.typename(), 'Geometry')
    
    def test_default_value(self):
        """Test de la valeur par défaut"""
        self.assertIsNone(self.geometry_type.default)
        self.assertIsNone(usertypes.get_type_default('Geometry'))
    
    def test_convert_valid_wkt_point(self):
        """Test conversion de points WKT valides"""
        valid_points = [
            'POINT(2.3 48.8)',
            'POINT(-0.1 51.5)',  
            'POINT(0 0)',
            'POINT(139.7 35.7)',
            'point(2.3 48.8)',  # Case insensitive
            '  POINT(2.3 48.8)  ',  # Whitespace
        ]
        
        for wkt in valid_points:
            with self.subTest(wkt=wkt):
                result = Geometry.do_convert(wkt)
                self.assertIsInstance(result, str)
                self.assertTrue(result.strip().upper().startswith('POINT'))
    
    def test_convert_valid_wkt_polygon(self):
        """Test conversion de polygones WKT valides"""
        polygon = 'POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))'
        result = Geometry.do_convert(polygon)
        self.assertEqual(result, polygon)
        
        # Test avec espaces et casse
        polygon_mixed = '  polygon((0 0, 1 0, 1 1, 0 1, 0 0))  '
        result = Geometry.do_convert(polygon_mixed)
        self.assertIsInstance(result, str)
    
    def test_convert_valid_wkt_linestring(self):
        """Test conversion de lignes WKT valides"""
        linestring = 'LINESTRING(0 0, 1 1, 2 2)'
        result = Geometry.do_convert(linestring)
        self.assertEqual(result, linestring)
    
    def test_convert_multigeometry(self):
        """Test conversion de géométries multiples"""
        multi_types = [
            'MULTIPOINT((0 0), (1 1))',
            'MULTILINESTRING((0 0, 1 1), (2 2, 3 3))',
            'MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))',
            'GEOMETRYCOLLECTION(POINT(0 0), LINESTRING(0 0, 1 1))'
        ]
        
        for wkt in multi_types:
            with self.subTest(wkt=wkt):
                result = Geometry.do_convert(wkt)
                self.assertIsInstance(result, str)
                self.assertIn(result.split('(')[0].upper(), 
                             ['MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION'])
    
    def test_convert_none_and_empty(self):
        """Test conversion de valeurs nulles et vides"""
        self.assertIsNone(Geometry.do_convert(None))
        self.assertIsNone(Geometry.do_convert(''))
        self.assertIsNone(Geometry.do_convert('   '))
    
    def test_convert_geojson_point(self):
        """Test conversion de GeoJSON vers WKT"""
        geojson_point = {
            'type': 'Point',
            'coordinates': [2.3, 48.8]
        }
        
        result = Geometry.do_convert(geojson_point)
        self.assertEqual(result, 'POINT(2.3 48.8)')
    
    def test_convert_geojson_invalid(self):
        """Test conversion de GeoJSON invalide"""
        invalid_geojson = {
            'type': 'Point',
            'coordinates': [2.3]  # Manque la coordonnée Y
        }
        
        with self.assertRaises(ConversionError):
            Geometry.do_convert(invalid_geojson)
    
    def test_convert_shapely_object(self):
        """Test conversion d'objets Shapely (mock)"""
        class MockShapelyObject:
            @property
            def __geo_interface__(self):
                return {'type': 'Point', 'coordinates': [1.0, 2.0]}
        
        shapely_obj = MockShapelyObject()
        result = Geometry.do_convert(shapely_obj)
        self.assertEqual(result, 'POINT(1.0 2.0)')
    
    def test_convert_invalid_wkt(self):
        """Test conversion de WKT invalides lève ConversionError"""
        invalid_wkt = [
            'INVALID(1 2)',
            'POINT()',
            'POINT(1)',
            'POLYGON()',
            '123',
            'text',
            'POINT(a b)',
        ]
        
        for wkt in invalid_wkt:
            with self.subTest(wkt=wkt):
                with self.assertRaises(ConversionError):
                    Geometry.do_convert(wkt)
    
    def test_convert_invalid_types(self):
        """Test conversion de types invalides"""
        invalid_types = [123, 45.67, True, [], {}]
        
        for value in invalid_types:
            with self.subTest(value=value):
                with self.assertRaises(ConversionError):
                    Geometry.do_convert(value)
    
    def test_is_right_type(self):
        """Test validation du type correct"""
        # Valid types
        self.assertTrue(Geometry.is_right_type(None))
        self.assertTrue(Geometry.is_right_type('POINT(0 0)'))
        self.assertTrue(Geometry.is_right_type('POLYGON((0 0, 1 0, 1 1, 0 0))'))
        
        # Invalid types
        self.assertFalse(Geometry.is_right_type(123))
        self.assertFalse(Geometry.is_right_type('invalid'))
        self.assertFalse(Geometry.is_right_type({}))
        self.assertFalse(Geometry.is_right_type([]))
    
    def test_wkt_validation_helper(self):
        """Test de la méthode de validation WKT interne"""
        # Valid WKT
        self.assertTrue(Geometry._is_valid_wkt('POINT(0 0)'))
        self.assertTrue(Geometry._is_valid_wkt('LINESTRING(0 0, 1 1)'))
        self.assertTrue(Geometry._is_valid_wkt('polygon((0 0, 1 0, 1 1, 0 0))'))
        
        # Invalid WKT
        self.assertFalse(Geometry._is_valid_wkt('INVALID(0 0)'))
        self.assertFalse(Geometry._is_valid_wkt(''))
        self.assertFalse(Geometry._is_valid_wkt(None))
        self.assertFalse(Geometry._is_valid_wkt(123))


class TestVectorType(unittest.TestCase):
    """Tests pour le type Vector - embeddings et vecteurs numériques"""
    
    def setUp(self):
        self.vector_type = Vector()
    
    def test_typename(self):
        """Test que le nom du type est correct"""
        self.assertEqual(Vector.typename(), 'Vector')
    
    def test_default_value(self):
        """Test de la valeur par défaut"""
        self.assertIsNone(self.vector_type.default)
        self.assertIsNone(usertypes.get_type_default('Vector'))
    
    def test_convert_list_of_numbers(self):
        """Test conversion de listes de nombres"""
        test_vectors = [
            [1, 2, 3],
            [0.1, 0.2, 0.3],
            [1.0, -2.5, 3.14159],
            [-1, -2, -3],
            [0],
            [1.5, 2.5, 3.5, 4.5, 5.5],  # Dimension 5
        ]
        
        for vector in test_vectors:
            with self.subTest(vector=vector):
                result = Vector.do_convert(vector)
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), len(vector))
                for i, val in enumerate(result):
                    self.assertAlmostEqual(val, vector[i], places=5)
    
    def test_convert_tuple_of_numbers(self):
        """Test conversion de tuples de nombres"""
        test_vectors = [
            (1, 2, 3),
            (0.1, 0.2, 0.3),
            (42,),
        ]
        
        for vector in test_vectors:
            with self.subTest(vector=vector):
                result = Vector.do_convert(vector)
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), len(vector))
                self.assertEqual(result, list(vector))
    
    def test_convert_json_string(self):
        """Test conversion de chaînes JSON"""
        json_vectors = [
            '[1, 2, 3]',
            '[0.1, 0.2, 0.3]',
            '[-1.5, 2.5, -3.5]',
            '[42]',
            '  [1, 2, 3]  ',  # Avec espaces
        ]
        
        for json_str in json_vectors:
            with self.subTest(json_str=json_str):
                result = Vector.do_convert(json_str)
                expected = json.loads(json_str.strip())
                self.assertEqual(result, expected)
    
    def test_convert_csv_string(self):
        """Test conversion de chaînes CSV"""
        csv_vectors = [
            '1,2,3',
            '0.1,0.2,0.3',
            '-1.5, 2.5, -3.5',  # Avec espaces
            '42',
            '  1,  2,  3  ',  # Avec espaces multiples
        ]
        
        for csv_str in csv_vectors:
            with self.subTest(csv_str=csv_str):
                result = Vector.do_convert(csv_str)
                expected = [float(x.strip()) for x in csv_str.split(',')]
                self.assertEqual(result, expected)
    
    def test_convert_none_and_empty(self):
        """Test conversion de valeurs nulles et vides"""
        self.assertIsNone(Vector.do_convert(None))
        self.assertIsNone(Vector.do_convert(''))
        self.assertIsNone(Vector.do_convert('   '))
    
    def test_convert_dimension_validation(self):
        """Test validation des dimensions si spécifiées"""
        vector_with_dim = Vector(dimensions=3)
        
        # Valid dimension
        result = vector_with_dim.convert([1, 2, 3])
        self.assertEqual(result, [1.0, 2.0, 3.0])
        
        # Invalid dimension should raise error
        with self.assertRaises(ValueError):
            vector_with_dim.convert([1, 2])  # Too short
        
        with self.assertRaises(ValueError):
            vector_with_dim.convert([1, 2, 3, 4])  # Too long
    
    def test_convert_mixed_types(self):
        """Test conversion de listes avec types mixtes"""
        mixed_vectors = [
            [1, 2.0, 3],  # int et float
            ['1', '2', '3'],  # strings numériques
            [1, '2.5', 3.0],  # mixte
        ]
        
        expected_results = [
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [1.0, 2.5, 3.0],
        ]
        
        for vector, expected in zip(mixed_vectors, expected_results):
            with self.subTest(vector=vector):
                result = Vector.do_convert(vector)
                self.assertEqual(result, expected)
    
    def test_convert_invalid_json(self):
        """Test conversion de JSON invalide"""
        invalid_json = [
            '[1, 2, 3',  # Bracket manquant
            '1, 2, 3]',  # Bracket manquant
            '[1, 2, abc]',  # Valeur non numérique
            'not json',
        ]
        
        for json_str in invalid_json:
            with self.subTest(json_str=json_str):
                with self.assertRaises(ConversionError):
                    Vector.do_convert(json_str)
    
    def test_convert_invalid_csv(self):
        """Test conversion de CSV invalide"""
        invalid_csv = [
            '1,2,abc',  # Valeur non numérique
            'a,b,c',  # Toutes non numériques
        ]
        
        for csv_str in invalid_csv:
            with self.subTest(csv_str=csv_str):
                with self.assertRaises(ConversionError):
                    Vector.do_convert(csv_str)
    
    def test_convert_invalid_types(self):
        """Test conversion de types complètement invalides"""
        invalid_types = [
            123,  # Nombre seul
            True,  # Boolean
            {},  # Dict vide
            object(),  # Objet arbitraire
        ]
        
        for value in invalid_types:
            with self.subTest(value=value):
                with self.assertRaises(ConversionError):
                    Vector.do_convert(value)
    
    def test_is_right_type(self):
        """Test validation du type correct"""
        # Valid types
        self.assertTrue(Vector.is_right_type(None))
        self.assertTrue(Vector.is_right_type([1, 2, 3]))
        self.assertTrue(Vector.is_right_type([]))
        self.assertTrue(Vector.is_right_type([0.1, 0.2, 0.3]))
        
        # Invalid types
        self.assertFalse(Vector.is_right_type(123))
        self.assertFalse(Vector.is_right_type('string'))
        self.assertFalse(Vector.is_right_type({}))
        self.assertFalse(Vector.is_right_type(True))
    
    def test_large_vectors(self):
        """Test performance avec de gros vecteurs (ex: OpenAI embeddings)"""
        # Test vecteur 1536 dimensions (OpenAI ada-002)
        large_vector = list(range(1536))
        result = Vector.do_convert(large_vector)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1536)
        self.assertEqual(result, [float(i) for i in range(1536)])
    
    def test_edge_cases(self):
        """Test de cas limites"""
        edge_cases = [
            ([float('inf')], [float('inf')]),  # Infinity
            ([float('-inf')], [float('-inf')]),  # Negative infinity
            # NaN is more complex, may want to handle specially
        ]
        
        for input_vec, expected in edge_cases:
            with self.subTest(input_vec=input_vec):
                result = Vector.do_convert(input_vec)
                if float('inf') in expected:
                    self.assertTrue(float('inf') in result or float('-inf') in result)
                else:
                    self.assertEqual(result, expected)


class TestTypeIntegration(unittest.TestCase):
    """Tests d'intégration pour les nouveaux types dans l'écosystème Grist"""
    
    def test_type_defaults_consistency(self):
        """Test que les valeurs par défaut sont cohérentes"""
        from sandbox.grist.usertypes import _type_defaults
        
        self.assertIn('Geometry', _type_defaults)
        self.assertIn('Vector', _type_defaults)
        self.assertIsNone(_type_defaults['Geometry'])
        self.assertIsNone(_type_defaults['Vector'])
    
    def test_type_registration(self):
        """Test que les types sont bien enregistrés"""
        # Test que les classes existent et sont instanciables
        geometry = Geometry()
        vector = Vector()
        
        self.assertIsInstance(geometry, usertypes.BaseColumnType)
        self.assertIsInstance(vector, usertypes.BaseColumnType)
    
    def test_alttext_handling(self):
        """Test gestion des AltText (valeurs d'erreur)"""
        geometry = Geometry()
        vector = Vector()
        
        # Les AltText doivent être préservés par convert()
        alt_text = AltText('Error message', 'POINT(0 0)')
        
        # Test avec Geometry
        result_geom = geometry.convert(alt_text)
        self.assertIsInstance(result_geom, AltText)
        
        # Test avec Vector  
        alt_text_vec = AltText('Error message', [1, 2, 3])
        result_vec = vector.convert(alt_text_vec)
        self.assertIsInstance(result_vec, AltText)


if __name__ == '__main__':
    # Configuration pour tests détaillés
    unittest.main(verbosity=2, buffer=True)
