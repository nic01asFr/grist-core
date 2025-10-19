"""
The basic types in Grist include Numeric, Text, Reference, Date, and others. Each type needs a
representation in storage (database), in communication messages, and in the memory of JS and
Python interpreters. Each type also needs a convenient Python representation when used in
formulas. Any typed column may also contain values of a wrong type, and those also need a
representation. Finally, every type defines a default value, used when the column is first
created, and for new records.

For values of type int or bool, It's possible to save some memory by using JS typed arrays or
Python's array.array. However, at least on the Python side, it means that we need an additional
data structure for values of the wrong type, and the memory savings aren't that great to be worth
the extra complexity.
"""
# pylint: disable=unidiomatic-typecheck
import csv
import datetime
import io
import json
import logging
import math
import os
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Union, Tuple

import depend
import objtypes
from objtypes import AltText, is_int_short
import moment
from records import Record, RecordSet

log = logging.getLogger(__name__)

NoneType = type(None)

# Note that this matches the defaults in app/common/gristTypes.js
_type_defaults = {
  'Any':          None,
  'Attachments':  None,
  'Blob':         None,
  'Bool':         False,
  'Choice':       u'',
  'ChoiceList':   None,
  'Date':         None,
  'DateTime':     None,
  'Geometry':     None,
  'Id':           0,
  'Int':          0,
  'ManualSortPos':  float('inf'),
  'Numeric':      0.0,
  'PositionNumber': float('inf'),
  'Ref':          0,
  'RefList':      None,
  'Text':         u'',
  'Vector':       None,
}

# Compute truthy and falsy values for Bool type here so they are not
# recomputed for every Bool conversion.
# These are the default values, which can be extended by environment variables.
_truthy_values = {"true", "yes", "1"}
_falsy_values = {"false", "no", "0"}
# If the environment variables are set, extend the truthy and falsy values.
if extra_truthy_values := os.environ.get('GRIST_TRUTHY_VALUES', ''):
  _truthy_values |= set(extra_truthy_values.lower().split(','))
if extra_falsy_values := os.environ.get('GRIST_FALSY_VALUES', ''):
  _falsy_values |= set(extra_falsy_values.lower().split(','))

def get_pure_type(col_type):
  """
  Returns type to the first colon, i.e. strips suffix for Ref:, DateTime:, etc.
  """
  return col_type.split(':', 1)[0]

def get_type_default(col_type):
  return _type_defaults.get(get_pure_type(col_type), None)

def formulaType(grist_type):
  """
  formulaType(gristType) is a decorator which saves the type as the 'grist_type' attribute
  on the decorated formula function. It allows the formula columns to be typed.
  """
  def wrapper(method):
    method.grist_type = grist_type
    return method
  return wrapper

def get_referenced_table_id(col_type):
  if col_type.startswith("Ref:"):
    return col_type[4:]
  if col_type.startswith("RefList:"):
    return col_type[8:]
  return None

def is_compatible_ref_type(type1, type2):
  """
  Returns whether type1 and type2 are Ref or RefList types with the same target table.
  """
  ref_table1 = get_referenced_table_id(type1)
  ref_table2 = get_referenced_table_id(type2)
  return bool(ref_table1 and ref_table1 == ref_table2)

def ifError(value, value_if_error):
  """
  Return `value` if it is valid, or `value_if_error` otherwise. Similar to Excel's IFERROR.
  """
  # TODO: this should ideally handle exception values and values of wrong type returned by
  # formulas, but it's unclear how to make that work.
  return value_if_error if isinstance(value, AltText) else value

_numeric_types = (float, int)
_numeric_or_none = (float, int, NoneType)

# Unique sentinel object to tell BaseColumnType constructor to use get_type_default().
_use_type_default = object()


class BaseColumnType(object):
  """
  Base class for all column types.
  """
  _global_creation_order = 0

  def __init__(self, default=_use_type_default):
    self.default = get_type_default(self.typename()) if default is _use_type_default else default
    self.default_func = None

    # Slightly silly, but it allows us to extract the order in which fields are listed in the
    # model definition, without looking back at the schema.
    self._creation_order = BaseColumnType._global_creation_order
    BaseColumnType._global_creation_order += 1

  @classmethod
  def typename(cls):
    """
    Returns the name of the type, e.g. "Int", "Ref", or "RefList".
    """
    return cls.__name__

  @classmethod
  def is_right_type(cls, _value):
    """
    Returns whether the given value belongs to this type. A cell may contain a wrong-type value
    (e.g. alttext, error), but formulas will only see right-type values, defaulting to the
    column's default.

    If is_right_type returns true, it must be possible to store the value (so with typed arrays,
    it must fit the type's restrictions).
    """
    return True

  @classmethod
  def do_convert(cls, value):
    """
    Converts a value of any type to one of our type (for which is_right_type is true) and returns
    it, or throws an exception. This is the method that should be overridden by subclasses.
    """
    return value

  def convert(self, value_to_convert):
    """
    Converts a value of any type to this type, returning either a value of the right type, or
    alttext, or error. It never throws, and should not be overridden by subclasses (override
    do_convert instead).
    """
    # Don't try to convert errors, although some day we may want to attempt it (e.g. if an error
    # contains original text, we may want to try to convert the original text).
    if isinstance(value_to_convert, objtypes.RaisedException):
      return value_to_convert

    try:
      return self.do_convert(value_to_convert)
    except Exception as e:
      # If conversion failed, return a string to serve as alttext.
      try:
        return str(value_to_convert)
      except Exception:
        # If converting to string failed, we should still produce something.
        return objtypes.safe_repr(value_to_convert)


class Text(BaseColumnType):
  """
  Text is the type for a field holding string (text) data.
  """
  @classmethod
  def do_convert(cls, value):
    if isinstance(value, bytes):
      return value.decode('utf8')
    elif value is None:
      return None
    elif isinstance(value, float) and not (math.isinf(value) or math.isnan(value)):
      # Format as integer if possible to avoid scientific notation
      # so that strings of digits that aren't meant to represent numbers convert correctly.
      # https://stackoverflow.com/questions/1848700/biggest-integer-that-can-be-stored-in-a-double
      # says that 2^53+1 is the first integer that isn't accurately stored in a float,
      # and it looks like 2^53 so we can't trust that either ;)
      if abs(value) < 2 ** 53:
        as_int = int(value)
        if value == as_int:
          return str(as_int)

      # More than 15 digits of precision can make large numbers (e.g. 2^53+1) look as if
      # they're represented exactly when they're not
      return u"%.15g" % value
    else:
      return str(value)

  @classmethod
  def is_right_type(cls, value):
    return isinstance(value, (str, NoneType))


class Blob(BaseColumnType):
  """
  Blob hold binary data.
  """
  @classmethod
  def do_convert(cls, value):
    return value

  @classmethod
  def is_right_type(cls, value):
    return isinstance(value, (bytes, NoneType))


class Any(BaseColumnType):
  """
  Any is the type that can hold any kind of value. It's used to hold computed values.
  """
  @classmethod
  def do_convert(cls, value):
    # Convert AltText values to plain text when assigning to type Any.
    return str(value) if isinstance(value, AltText) else value


class Bool(BaseColumnType):
  """
  Bool is the type for a field holding boolean data.
  """
  @classmethod
  # We'll convert any falsy value to False, non-zero numbers to True, and only strings we
  # recognize.
  # The GRIST_TRUTHY_VALUES and GRIST_FALSY_VALUES environment variables
  # can be set to extend this list.
  # Everything else will result in alttext.
  def do_convert(cls, value):
    if not value:
      return False
    if isinstance(value, _numeric_types):
      return True
    if isinstance(value, AltText):
      value = str(value)
    if isinstance(value, str):
      if value.lower() in _falsy_values:
        return False
      if value.lower() in _truthy_values:
        return True
    raise objtypes.ConversionError("Bool")

  @classmethod
  def is_right_type(cls, value):
    return isinstance(value, (bool, NoneType))


class Int(BaseColumnType):
  """
  Int is the type for a field holding integer data.
  """
  @classmethod
  def do_convert(cls, value):
    if value in ("", None):
      return None
    # Convert to float first, since python does not allow casting strings with decimals to int
    ret = int(float(value))
    if not is_int_short(ret):
      raise OverflowError("Integer value too large")
    return ret

  @classmethod
  def is_right_type(cls, value):
    return value is None or (type(value) is int and is_int_short(value))


class Numeric(BaseColumnType):
  """
  Numeric is the type for a field holding numerical data.
  """
  @classmethod
  def do_convert(cls, value):
    return float(value) if value not in ("", None) else None

  @classmethod
  def is_right_type(cls, value):
    # TODO: Python distinguishes ints from floats, while JS only has floats. A value that can be
    # interpreted as an int will upon being entered have type 'float', but after database reload
    # will have type 'int'.
    return type(value) in _numeric_or_none


class Date(Numeric):
  """
  Date is the type for a field holding date data (no timezone).
  """
  @classmethod
  def do_convert(cls, value):
    if value in ("", None):
      return None
    elif isinstance(value, datetime.datetime):
      return moment.date_to_ts(value.date())
    elif isinstance(value, datetime.date):
      return moment.date_to_ts(value)
    elif isinstance(value, _numeric_types):
      return float(value)
    elif isinstance(value, str):
      # We also accept a date in ISO format (YYYY-MM-DD), the time portion is optional and ignored
      return moment.parse_iso_date(value)
    else:
      raise objtypes.ConversionError('Date')

  @classmethod
  def is_right_type(cls, value):
    return isinstance(value, _numeric_or_none)


class DateTime(Date):
  """
  DateTime is the type for a field holding date and time data.
  """
  def __init__(self, timezone="America/New_York", default=_use_type_default):
    super(DateTime, self).__init__(default)

    try:
      self.timezone = moment.Zone(timezone)
    except KeyError:
      self.timezone = moment.Zone('UTC')

  def do_convert(self, value):
    if value in ("", None):
      return None
    elif isinstance(value, datetime.datetime):
      return moment.dt_to_ts(value, self.timezone)
    elif isinstance(value, datetime.date):
      return moment.date_to_ts(value, self.timezone)
    elif isinstance(value, _numeric_types):
      return float(value)
    elif isinstance(value, str):
      # We also accept a datetime in ISO format (YYYY-MM-DD[T]HH:mm:ss)
      return moment.parse_iso(value, self.timezone)
    else:
      raise objtypes.ConversionError('DateTime')

class Choice(Text):
  """
  Choice is the type for a field holding one of a set of acceptable string (text) values.
  TODO: Type should possibly be aware of the allowed choices, and be considered invalid
    when its value isn't one of them
  """
  pass


class ChoiceList(BaseColumnType):
  """
  ChoiceList is the type for a field holding a list of strings from a set of acceptable choices.
  """
  def do_convert(self, value):
    if not value:
      return None
    elif isinstance(value, str):
      # If it's a string that looks like JSON, try to parse it as such.
      if value.startswith('['):
        try:
          return tuple(str(item) for item in json.loads(value))
        except Exception:
          pass
      return value
    else:
      # Accepts other kinds of iterables; if that doesn't work, fail the conversion too.
      return tuple(str(item) for item in value)

  @classmethod
  def is_right_type(cls, value):
    return value is None or (isinstance(value, (tuple, list)) and
                             all(isinstance(item, str) for item in value))

  @classmethod
  def toString(cls, value):
    if isinstance(value, (tuple, list)):
      try:
        buf = io.StringIO()
        csv.writer(buf).writerow(value)
        return buf.getvalue().strip()
      except Exception:
        pass
    return value


class PositionNumber(BaseColumnType):
  """
  PositionNumber is the type for a position field used to order records in record lists.
  """
  # The 'inf' default is used by prepare_new_values() in column.py, which always changes it to
  # finite numbers, but relies on it to keep newly-added records below existing ones by default.
  @classmethod
  def do_convert(cls, value):
    return float(value) if value not in ("", None) else float('inf')

  @classmethod
  def is_right_type(cls, value):
    # Same as Numeric, but does not support None.
    return type(value) in _numeric_types


class ManualSortPos(PositionNumber):
  pass


class Id(BaseColumnType):
  """
  Id is the type for the record ID field, present automatically in each table.
  The default of 0 points to the always-present empty record. Real records start at index 1.
  """
  @classmethod
  def do_convert(cls, value):
    # Just like Int.do_convert, but skips conversion via float. This also makes it work for Record
    # types, which override int() conversion to yield the row ID. Arbitrary values should not be
    # cast to ints as it results in false hits when converting numerical values to reference ids.
    if not value:
      return 0
    if not isinstance(value, (int, Record)):
      raise TypeError("Cannot convert to Id type")
    ret = int(value)
    if not is_int_short(ret):
      raise OverflowError("Integer value too large")
    return ret

  @classmethod
  def is_right_type(cls, value):
    return (type(value) is int and is_int_short(value))


class Reference(Id):
  """
  Reference is the type for a field holding a reference into another table.

  Note that if `foo` is a Reference('Foo'), then `rec.foo` is of type `Foo.Record`. The ID of that
  record is available as `rec.foo._row_id`. It is equivalent to `rec.foo.id`, except that
  accessing `id`, as other public properties, involves a lookup in `Foo` table.
  """
  def __init__(self, table_id, reverse_of=None):
    super(Reference, self).__init__()
    self.table_id = table_id
    self._reverse_col_id = reverse_of

  @classmethod
  def typename(cls):
    return "Ref"

  def reverse_source_node(self):
    """ Returns the reverse column as depend.Node, if it exists. """
    return depend.Node(self.table_id, self._reverse_col_id) if self._reverse_col_id else None

class ReferenceList(BaseColumnType):
  """
  ReferenceList stores a list of references into another table.
  """
  def __init__(self, table_id, reverse_of=None):
    super(ReferenceList, self).__init__()
    self.table_id = table_id
    self._reverse_col_id = reverse_of

  @classmethod
  def typename(cls):
    return "RefList"

  def reverse_source_node(self):
    """ Returns the reverse column as depend.Node, if it exists. """
    return depend.Node(self.table_id, self._reverse_col_id) if self._reverse_col_id else None

  def do_convert(self, value):
    if isinstance(value, str):
      # This is second part of a "hack" we have to do when we rename tables. During
      # the rename, we briefly change all Ref columns to Int columns (to lose the table
      # part), and then back to Ref columns. The values during this change are stored
      # as serialized strings, which we expect to understand when the column is back to
      # being a Ref column. We can either end up with a list of ints, or a RecordList
      # serialized as a string.
      # TODO: explain why we need to do this and why we have chosen the Int column
      try:
        # If it's a string that looks like JSON, try to parse it as such.
        if value.startswith('['):
          parsed = json.loads(value)
          # It must be list of integers, and all of them must be positive integers.
          if (isinstance(parsed, list) and
              all(isinstance(v, int) and v > 0 for v in parsed)):
            value = parsed
        else:
        # Else try to parse it as a RecordList
          value = objtypes.RecordList.from_repr(value)
      except Exception:
        pass

    if isinstance(value, RecordSet):
      assert value._table.table_id == self.table_id
      return objtypes.RecordList(value._row_ids, group_by=value._group_by, sort_by=value._sort_by,
          sort_key=value._sort_key)
    elif not value:
      # Represent an empty ReferenceList as None (also its default value). Formulas will see [].
      return None

    # We can also have a list of RecordSet, in that case just flatten this list. This is used by
    # formulas like `Table1.lookupRecords().OtherRecords' which returns a list of RecordSets.
    elif isinstance(value, list) and all(
         isinstance(rset, RecordSet) and rset._table.table_id == self.table_id for rset in value
      ):
      row_ids_flat_list = [rec.id for rset in value for rec in rset]
      row_ids_unique_list = list(OrderedDict((el, None) for el in row_ids_flat_list).keys())
      return row_ids_unique_list

    return [Reference.do_convert(val) for val in value]

  @classmethod
  def is_right_type(cls, value):
    # TODO: whenever is_right_type isn't trivial, get_cell_value should just remember the result
    # rather than recompute it on every access. Actually this applies not only to is_right_type
    # but to everything get_cell_value does. It should use minimal-memory minimal-overhead
    # translations of raw->rich for valid values, and use what memory it needs but still guarantee
    # constant time for invalid values.
    return (value is None or
        (isinstance(value, objtypes.RecordList)) or
        (isinstance(value, list) and all(Reference.is_right_type(val) for val in value))
    )


class Attachments(ReferenceList):
  """
  Currently attachment type is the field for holding data for attachments.
  """
  def __init__(self):
    super(Attachments, self).__init__('_grist_Attachments')


class Geometry(BaseColumnType):
  """
  Geometry type for holding PostGIS spatial data (points, lines, polygons, etc.).
  Values are stored as WKT (Well-Known Text) strings for compatibility.
  
  Supports:
  - WKT strings: POINT, LINESTRING, POLYGON, MULTIPOINT, etc.
  - GeoJSON dictionaries (basic conversion)
  - Shapely objects (via __geo_interface__)
  
  Examples:
    >>> Geometry.do_convert('POINT(2.3 48.8)')
    'POINT(2.3 48.8)'
    >>> Geometry.do_convert({'type': 'Point', 'coordinates': [2.3, 48.8]})
    'POINT(2.3 48.8)'
  """
  
  @classmethod
  def do_convert(cls, value: Any) -> Optional[str]:
    """
    Convert various input types to WKT string format.
    
    Args:
        value: Input value (WKT string, GeoJSON dict, Shapely object, or None)
        
    Returns:
        WKT string representation or None for empty values
        
    Raises:
        objtypes.ConversionError: If input cannot be converted to valid geometry
    """
    if value in ("", None):
      return None
    elif isinstance(value, str):
      # Accept WKT strings directly
      if cls._is_valid_wkt(value):
        return value.strip()
      else:
        raise objtypes.ConversionError('Geometry')
    elif isinstance(value, dict):
      # Convert GeoJSON to WKT if possible
      return cls._geojson_to_wkt(value)
    elif hasattr(value, '__geo_interface__'):
      # Handle Shapely objects
      return cls._geojson_to_wkt(value.__geo_interface__)
    else:
      raise objtypes.ConversionError('Geometry')

  @classmethod
  def is_right_type(cls, value: Any) -> bool:
    """
    Check if value is a valid WKT string or None.
    
    Args:
        value: Value to validate
        
    Returns:
        True if value is None or a valid WKT string
    """
    return value is None or (isinstance(value, str) and cls._is_valid_wkt(value))

  @staticmethod
  def _is_valid_wkt(wkt_string: Any) -> bool:
    """
    Basic validation for WKT format.
    
    Args:
        wkt_string: String to validate as WKT
        
    Returns:
        True if string appears to be valid WKT format
    """
    if not isinstance(wkt_string, str):
      return False
    wkt_upper = wkt_string.strip().upper()
    wkt_types = ['POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT', 
                 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION']
    return any(wkt_upper.startswith(wkt_type) for wkt_type in wkt_types)

  @staticmethod
  def _geojson_to_wkt(geojson: Dict[str, Any]) -> str:
    """
    Basic GeoJSON to WKT conversion.
    
    Currently supports only Point geometry type.
    
    Args:
        geojson: GeoJSON-like dictionary
        
    Returns:
        WKT string representation
        
    Raises:
        objtypes.ConversionError: If GeoJSON cannot be converted
    """
    if geojson.get('type') == 'Point' and 'coordinates' in geojson:
      coords = geojson['coordinates']
      if len(coords) >= 2:
        return f"POINT({coords[0]} {coords[1]})"
    raise objtypes.ConversionError('Geometry')


class Vector(BaseColumnType):
  """
  Vector type for holding pg_vector embeddings and numeric vectors.
  Values are stored as arrays of floating-point numbers.
  
  Supports:
  - Lists/tuples of numbers: [1.0, 2.0, 3.0]
  - JSON string arrays: "[1.0, 2.0, 3.0]"
  - CSV string format: "1.0, 2.0, 3.0"
  - Mixed numeric types (int, float, numeric strings)
  - Dimension validation (optional)
  
  Common use cases:
  - OpenAI embeddings (1536 dimensions)
  - Sentence transformers (384 dimensions) 
  - Custom ML model embeddings
  - Mathematical vectors of any size
  
  Examples:
    >>> Vector.do_convert([1, 2, 3])
    [1.0, 2.0, 3.0]
    >>> Vector.do_convert("[0.1, 0.2, 0.3]")
    [0.1, 0.2, 0.3]
    >>> Vector.do_convert("1.5, -2.0, 3.14")
    [1.5, -2.0, 3.14]
  """
  
  def __init__(self, dimensions: Optional[int] = None) -> None:
    """
    Initialize Vector type with optional dimension constraint.
    
    Args:
        dimensions: Expected vector dimension, or None for any size
    """
    super(Vector, self).__init__()
    self.dimensions = dimensions

  @classmethod
  def do_convert(cls, value: Any) -> Optional[List[float]]:
    """
    Convert various input types to list of floats.
    
    Args:
        value: Input value (list, tuple, string, or None)
        
    Returns:
        List of float values, or None for empty inputs
        
    Raises:
        objtypes.ConversionError: If input cannot be converted to valid vector
    """
    if value in ("", None):
      return None
    elif isinstance(value, (list, tuple)):
      # Convert to list of floats
      try:
        vector = [float(x) for x in value]
        return vector
      except (ValueError, TypeError):
        raise objtypes.ConversionError('Vector')
    elif isinstance(value, str):
      # Parse string representation like "[1.0, 2.0, 3.0]" or "1.0, 2.0, 3.0"
      value_stripped = value.strip()
      if not value_stripped:
        return None
      
      try:
        if value_stripped.startswith('[') and value_stripped.endswith(']'):
          # JSON array format
          import json
          vector = json.loads(value_stripped)
          if not isinstance(vector, list):
            raise ValueError("JSON must be an array")
          return [float(x) for x in vector]
        else:
          # Comma-separated values format
          vector = [float(x.strip()) for x in value_stripped.split(',')]
          return vector
      except (ValueError, TypeError, json.JSONDecodeError):
        raise objtypes.ConversionError('Vector')
    else:
      raise objtypes.ConversionError('Vector')

  def convert(self, value_to_convert: Any) -> Union[List[float], AltText, None]:
    """
    Override base convert to add dimension validation.
    
    Args:
        value_to_convert: Value to convert and validate
        
    Returns:
        Converted vector, AltText for dimension errors, or None
    """
    converted = super(Vector, self).convert(value_to_convert)
    if (converted is not None and 
        self.dimensions is not None and 
        len(converted) != self.dimensions):
      return AltText(
        f"Vector dimension mismatch: expected {self.dimensions}, got {len(converted)}",
        converted
      )
    return converted

  @classmethod
  def is_right_type(cls, value: Any) -> bool:
    """
    Check if value is a valid vector (list/tuple of numbers) or None.
    
    Args:
        value: Value to validate
        
    Returns:
        True if value is None or a list/tuple of numeric values
    """
    return (value is None or 
            (isinstance(value, (list, tuple)) and 
             all(isinstance(x, _numeric_types) for x in value)))



# ============================================================================
# FORMULES GÉOMÉTRIQUES NATIVES POUR GRIST
# ============================================================================

def ST_DISTANCE(geom1: str, geom2: str, unit: str = 'm') -> float:
  """
  Calcule la distance entre deux géométries.
  
  Args:
      geom1, geom2: Géométries au format WKT
      unit: Unité ('m', 'km', 'deg') - défaut: mètres
  
  Returns:
      Distance en unité spécifiée
  
  Example:
      ST_DISTANCE($Location_A, $Location_B, 'km')
  """
  try:
      coords1 = _extract_point_coords(geom1)
      coords2 = _extract_point_coords(geom2)
      
      if not coords1 or not coords2:
          raise ValueError("Géométries non supportées pour ST_DISTANCE")
      
      # Distance haversine pour coordonnées géographiques
      distance_m = _haversine_distance(coords1, coords2)
      
      if unit == 'km':
          return distance_m / 1000
      elif unit == 'deg':
          return _euclidean_distance(coords1, coords2)
      else:
          return distance_m
          
  except Exception as e:
      raise ValueError(f"ST_DISTANCE error: {e}")


def ST_AREA(geometry: str, unit: str = 'm2') -> float:
  """
  Calcule l'aire d'un polygone.
  
  Args:
      geometry: Polygone au format WKT
      unit: Unité ('m2', 'km2', 'ha') - défaut: m²
  
  Example:
      ST_AREA($Polygon_Field, 'ha')
  """
  try:
      coords = _extract_polygon_coords(geometry)
      if not coords:
          raise ValueError("Géométrie n'est pas un polygone valide")
      
      area_m2 = _polygon_area_m2(coords)
      
      if unit == 'km2':
          return area_m2 / 1000000
      elif unit == 'ha':
          return area_m2 / 10000
      else:
          return area_m2
          
  except Exception as e:
      raise ValueError(f"ST_AREA error: {e}")


def ST_CONTAINS(geom1: str, geom2: str) -> bool:
  """
  Teste si geom1 contient entièrement geom2.
  
  Args:
      geom1: Géométrie contenante (généralement polygone)
      geom2: Géométrie contenue (généralement point)
  
  Example:
      ST_CONTAINS($Zone_Polygon, $Location_Point)
  """
  try:
      if "POLYGON" in geom1.upper() and "POINT" in geom2.upper():
          polygon = _extract_polygon_coords(geom1)
          point = _extract_point_coords(geom2)
          return _point_in_polygon(point, polygon) if point and polygon else False
      
      return False  # Autres cas non supportés pour l'instant
      
  except Exception as e:
      raise ValueError(f"ST_CONTAINS error: {e}")


def ST_CENTROID(geometry: str) -> str:
  """
  Calcule le centroïde (centre géométrique) d'une géométrie.
  
  Args:
      geometry: Géométrie au format WKT
  
  Returns:
      Point WKT du centroïde
  
  Example:
      ST_CENTROID($Polygon_Field)
  """
  try:
      if "POLYGON" in geometry.upper():
          coords = _extract_polygon_coords(geometry)
          if not coords:
              raise ValueError("Polygone invalide")
          
          # Centroïde = moyenne des coordonnées
          center_x = sum(x for x, y in coords) / len(coords)
          center_y = sum(y for x, y in coords) / len(coords)
          
          return f"POINT({center_x} {center_y})"
      
      elif "POINT" in geometry.upper():
          return geometry  # Déjà un point
          
      raise ValueError("Type de géométrie non supporté")
      
  except Exception as e:
      raise ValueError(f"ST_CENTROID error: {e}")


def VECTOR_SIMILARITY(vector1, vector2, method: str = 'cosine') -> float:
  """
  Calcule la similarité entre deux vecteurs.

  Args:
      vector1, vector2: Vecteurs à comparer
      method: Méthode ('cosine', 'euclidean', 'dot') - défaut: cosine

  Returns:
      Score de similarité (0-1 pour cosine)

  Example:
      VECTOR_SIMILARITY($Embedding_A, $Embedding_B)
  """
  try:
      if not vector1 or not vector2 or len(vector1) != len(vector2):
          raise ValueError("Vecteurs doivent avoir la même dimension")

      if method == 'cosine':
          return _cosine_similarity(vector1, vector2)
      elif method == 'euclidean':
          return 1 / (1 + _euclidean_distance_vectors(vector1, vector2))
      elif method == 'dot':
          return sum(a * b for a, b in zip(vector1, vector2))
      else:
          raise ValueError(f"Méthode {method} non supportée")

  except Exception as e:
      raise ValueError(f"VECTOR_SIMILARITY error: {e}")


def VECTOR_SEARCH(table, query: str, threshold: float = 0.75, limit: int = 20, embedding_column: str = None):
  """
  Name: VECTOR_SEARCH
  Usage: __VECTOR_SEARCH__(table, query, threshold=0.75, limit=20, embedding_column=None)

  Recherche sémantique par similarité vectorielle dans une table.
  Convertit automatiquement la requête texte en embedding et compare avec les enregistrements.
  Retourne les résultats les plus pertinents selon la similarité cosinus.

  Args:
      table: Table dans laquelle effectuer la recherche (ex: Students, WebDAV_Files)
      query: Texte de recherche ou référence de colonne (ex: "contrats RH" ou $description)
      threshold: Seuil de similarité minimum (0.0 à 1.0, défaut: 0.75)
                 0.7-0.8 = similaire, 0.8-0.9 = très similaire, 0.9+ = quasi-identique
      limit: Nombre maximum de résultats à retourner (défaut: 20)
      embedding_column: Nom de la colonne Vector à utiliser (optionnel)
                       - Si None: utilise grist_record_embedding (auto-embedding de tous les champs)
                       - Si spécifié: utilise une colonne Vector custom créée avec CREATE_VECTOR()

  Returns:
      list[int]: Liste d'IDs de records (compatible avec type Reference List)
                 Liste vide [] si aucun résultat ou query vide

  Examples:
      ```
      # Recherche basique avec auto-embedding (tous les champs texte)
      VECTOR_SEARCH(WebDAV_Files, "contrats de travail")

      # Recherche dans une colonne Vector custom (champs spécifiques)
      VECTOR_SEARCH(WebDAV_Files, "rapport annuel", embedding_column="A")

      # Recherche avec seuil strict pour résultats très pertinents
      VECTOR_SEARCH(Documents, "factures 2024", threshold=0.85, limit=5)

      # Utiliser le contenu d'une colonne comme requête
      VECTOR_SEARCH(WebDAV_Files, $ai_summary, threshold=0.3, limit=3, embedding_column="A")

      # Recherche sémantique large avec seuil bas
      VECTOR_SEARCH(Knowledge_Base, $user_question, threshold=0.6, limit=10)

      # Trouver documents similaires au document courant
      VECTOR_SEARCH(Documents, $title + " " + $summary, threshold=0.8, limit=5)
      ```

  Workflow complet - Auto-embedding (par défaut):
      1. Le système génère automatiquement grist_record_embedding pour chaque record
      2. Tous les champs texte sont combinés pour créer l'embedding
      3. VECTOR_SEARCH(Table, "query") recherche dans ces embeddings automatiques
      4. Idéal pour recherche globale sans configuration

  Workflow complet - Custom embeddings:
      1. Créer colonne Vector (ex: colonne A de type "Vector")
      2. Formule dans colonne A: CREATE_VECTOR($champ1, $champ2)
      3. Créer colonne Reference List (ex: colonne B)
      4. Formule dans colonne B: VECTOR_SEARCH(Table, $query, embedding_column="A")
      5. Les résultats pointent vers les records les plus similaires

  Cas d'usage:
      - **Support client**: Trouver articles similaires à une question
      - **Gestion documentaire**: Rechercher documents par contenu sémantique
      - **Recommandations**: Suggérer contenus similaires
      - **Déduplication**: Identifier doublons sémantiques (threshold élevé)
      - **Classification**: Trouver catégorie par similarité d'exemples

  Notes techniques:
      - Similarité cosinus: mesure l'angle entre vecteurs (0=opposé, 1=identique)
      - Embeddings: vecteurs de 1024 dimensions via API Albert (IA française)
      - Query embedding: généré à la volée et mis en cache
      - Performance: O(n) où n = nombre de records (parcours linéaire)
      - Si query est vide/None, retourne liste vide []

  Comparaison auto-embedding vs custom:
      - Auto-embedding: Simple, aucune config, tous les champs, bon pour recherche globale
      - Custom embedding: Contrôle précis, recherches ciblées, meilleurs résultats
  """
  try:
      from embedding_manager import VECTOR_SEARCH_SYSTEM

      # Déterminer table_id
      table_id = None

      # Extraire table_id depuis l'objet table
      if hasattr(table, 'table') and hasattr(table.table, 'table_id'):
          table_id = table.table.table_id
      else:
          raise ValueError("Premier paramètre doit être une table (ex: WebDAV_Files)")

      # Vérifier que query n'est pas vide
      if not query or query is None:
          return []  # Retourner liste vide si pas de requête

      # Utiliser la colonne spécifiée ou la colonne par défaut
      if embedding_column is None:
          embedding_column = 'grist_record_embedding'
          log.info(f"VECTOR_SEARCH: table {table_id}, colonne par défaut {embedding_column}")
      else:
          log.info(f"VECTOR_SEARCH: table {table_id}, colonne custom {embedding_column}")

      # Appeler la fonction système avec la colonne spécifiée
      results = VECTOR_SEARCH_SYSTEM(
          table_id,
          query,
          limit=int(limit),
          threshold=float(threshold),
          embedding_column=embedding_column
      )

      # Retourner la liste des row_ids
      if results:
          return [int(r['row_id']) for r in results]
      else:
          return []

  except Exception as e:
      import traceback
      log.error(f"VECTOR_SEARCH error: {e}\n{traceback.format_exc()}")
      return []


# ============================================================================
# FONCTIONS UTILITAIRES GÉOMÉTRIQUES
# ============================================================================

def _extract_point_coords(wkt: str):
  """Extrait les coordonnées d'un point WKT."""
  import re
  match = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', wkt.upper())
  if match:
      return (float(match.group(1)), float(match.group(2)))
  return None


def _extract_polygon_coords(wkt: str):
  """Extrait les coordonnées d'un polygone WKT (anneau externe seulement)."""
  import re
  match = re.search(r'POLYGON\s*\(\s*\(\s*(.*?)\s*\)\s*\)', wkt.upper())
  if match:
      coords_str = match.group(1)
      coords = []
      for pair in coords_str.split(','):
          parts = pair.strip().split()
          if len(parts) >= 2:
              coords.append((float(parts[0]), float(parts[1])))
      return coords
  return None


def _haversine_distance(coord1, coord2) -> float:
  """Calcule la distance haversine entre deux points en mètres."""
  lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
  lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
  
  dlat = lat2 - lat1
  dlon = lon2 - lon1
  
  a = (math.sin(dlat / 2) ** 2 + 
       math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
  
  c = 2 * math.asin(math.sqrt(a))
  r = 6371000  # Rayon terre en mètres
  
  return r * c


def _euclidean_distance(coord1, coord2) -> float:
  """Distance euclidienne simple entre deux points."""
  return math.sqrt((coord2[0] - coord1[0]) ** 2 + (coord2[1] - coord1[1]) ** 2)


def _polygon_area_m2(coords) -> float:
  """Calcule l'aire d'un polygone en mètres carrés (approximation)."""
  if len(coords) < 3:
      return 0
  
  # Formule du lacet en coordonnées géographiques
  area_deg2 = 0
  n = len(coords)
  
  for i in range(n):
      j = (i + 1) % n
      area_deg2 += coords[i][0] * coords[j][1]
      area_deg2 -= coords[j][0] * coords[i][1]
  
  area_deg2 = abs(area_deg2) / 2
  
  # Conversion approximative degrés² → m²
  return area_deg2 * 12364000000  # m²


def _point_in_polygon(point, polygon) -> bool:
  """Test point-in-polygon par ray casting."""
  if not point or not polygon:
      return False
      
  x, y = point
  n = len(polygon)
  inside = False
  
  p1x, p1y = polygon[0]
  for i in range(1, n + 1):
      p2x, p2y = polygon[i % n]
      if y > min(p1y, p2y):
          if y <= max(p1y, p2y):
              if x <= max(p1x, p2x):
                  if p1y != p2y:
                      xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                  if p1x == p2x or x <= xinters:
                      inside = not inside
      p1x, p1y = p2x, p2y
  
  return inside


def _cosine_similarity(vecA, vecB) -> float:
  """Calcule la similarité cosinus entre deux vecteurs."""
  dot_product = sum(a * b for a, b in zip(vecA, vecB))
  magnitude_a = math.sqrt(sum(a * a for a in vecA))
  magnitude_b = math.sqrt(sum(b * b for b in vecB))
  
  if magnitude_a == 0 or magnitude_b == 0:
      return 0
  
  return dot_product / (magnitude_a * magnitude_b)


def _euclidean_distance_vectors(vecA, vecB) -> float:
  """Distance euclidienne entre deux vecteurs."""
  return math.sqrt(sum((a - b) ** 2 for a, b in zip(vecA, vecB)))


# ============================================================================
# CUSTOM EMBEDDINGS - CREATE_VECTOR()
# ============================================================================

def CREATE_VECTOR(*field_values):
  """
  Name: CREATE_VECTOR
  Usage: __CREATE_VECTOR__(*field_values)

  Génère un embedding vectoriel personnalisé à partir de champs sélectionnés.
  Contrairement à l'auto-embedding (qui utilise tous les champs texte), cette fonction
  permet de créer des embeddings ciblés pour des recherches sémantiques spécifiques.

  Args:
      *field_values: Valeurs des champs à combiner pour l'embedding
                     Accepte n'importe quel nombre de colonnes (ex: $col1, $col2, ...)
                     Les valeurs vides/None sont ignorées automatiquement

  Returns:
      list[float]: Vecteur embedding de 1024 dimensions (API Albert)
      None: Si aucun contenu valide ou génération en cours

  Examples:
      ```
      # Créer une colonne Vector pour rechercher par titre + résumé
      CREATE_VECTOR($file_name, $ai_summary)

      # Embedding basé uniquement sur le contenu extrait
      CREATE_VECTOR($extracted_content)

      # Embedding sur métadonnées (tags + catégorie + auteur)
      CREATE_VECTOR($ai_tags, $ai_category, $author)

      # Combinaison de plusieurs champs texte
      CREATE_VECTOR($title, $description, $keywords, $notes)
      ```

  Workflow d'utilisation:
      1. Créer une colonne de type "Vector" (ex: colonne A)
      2. Ajouter la formule CREATE_VECTOR($champ1, $champ2, ...)
      3. Les embeddings sont générés automatiquement (asynchrone)
      4. Utiliser avec VECTOR_SEARCH(..., embedding_column="A")

  Notes techniques:
      - Génération asynchrone via queue (non-bloquant, retry automatique)
      - Cache avec hash MD5 du contenu pour éviter régénération
      - Utilise l'API Albert (IA française) pour les embeddings
      - Compatible avec le type de colonne "Vector" de Grist
      - Les valeurs sont persistées automatiquement dans la colonne

  Cas d'usage:
      - Documents: Recherche par contenu ou métadonnées séparément
      - Produits: Recherche par nom vs recherche par description technique
      - Support: Recherche par question vs recherche par réponse
      - Multi-langues: Embeddings séparés par langue
  """
  from embedding_manager import _get_embedding_manager
  import hashlib

  # Concaténer les valeurs non-vides
  text_parts = []
  for value in field_values:
    if value is not None and value != '':
      text_parts.append(str(value))

  # Pas de contenu → pas d'embedding
  if not text_parts:
    return None

  combined_text = ' '.join(text_parts)

  # Calculer hash du contenu pour cache
  content_hash = hashlib.md5(combined_text.encode('utf-8')).hexdigest()

  # Essayer de récupérer depuis le cache mémoire du manager
  manager = _get_embedding_manager()
  if manager:
    try:
      # Générer l'embedding via le manager (qui gère le cache)
      embedding = manager.generate_embedding(combined_text, 'albert')

      if embedding:
        return embedding  # [1024 floats]
    except Exception as e:
      log.debug(f"CREATE_VECTOR: Génération embedding: {e}")

  # Pas encore généré ou erreur → retourner None
  # La formule sera recalculée automatiquement quand disponible
  return None