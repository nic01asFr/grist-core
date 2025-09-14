"""
This file packages together other modules needed for usercode in order to create
a consistent API accessible with only "import grist".
"""
# pylint: disable=unused-import

# These imports are used in processing generated usercode.
from usertypes import Any, Text, Blob, Int, Bool, Date, DateTime, \
  Numeric, Choice, ChoiceList, Id, Attachments, AltText, ifError, Geometry, Vector
from usertypes import PositionNumber, ManualSortPos, Reference, ReferenceList, formulaType
from usertypes import ST_DISTANCE, ST_AREA, ST_CONTAINS, ST_CENTROID, VECTOR_SIMILARITY
from table import UserTable
from records import Record, RecordSet
from column import SafeSortKey

# Expose spatial/vector functions globally for formulas
__all__ = [
    'Any', 'Text', 'Blob', 'Int', 'Bool', 'Date', 'DateTime',
    'Numeric', 'Choice', 'ChoiceList', 'Id', 'Attachments', 'AltText', 'ifError',
    'Geometry', 'Vector',
    'PositionNumber', 'ManualSortPos', 'Reference', 'ReferenceList', 'formulaType',
    'ST_DISTANCE', 'ST_AREA', 'ST_CONTAINS', 'ST_CENTROID', 'VECTOR_SIMILARITY',
    'UserTable', 'Record', 'RecordSet', 'SafeSortKey'
]

DOCS = [(__name__, (Record, RecordSet, UserTable)),
        ('lookup', (UserTable.lookupOne, UserTable.lookupRecords))]
