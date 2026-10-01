import io
import unittest

from anatomapa.readers.aggregate import aggregate_count, aggregate_sum
from anatomapa.readers.csv_reader import from_csv
from anatomapa.readers.json_reader import from_json
from anatomapa.readers.native import from_dict, from_records


class TestFromDict(unittest.TestCase):
    def test_basic(self):
        result = from_dict({"head": 10.0, "arm": 5.0})
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_int_values_converted(self):
        result = from_dict({"leg": 3})
        self.assertEqual(result, [("leg", 3.0)])
        self.assertIsInstance(result[0][1], float)

    def test_empty(self):
        self.assertEqual(from_dict({}), [])

    def test_stable_order(self):
        data = {"c": 3.0, "a": 1.0, "b": 2.0}
        result = from_dict(data)
        self.assertEqual([r[0] for r in result], ["c", "a", "b"])


class TestFromRecords(unittest.TestCase):
    def test_list_of_dicts(self):
        records = [
            {"region": "head", "value": 10},
            {"region": "arm", "value": 5},
        ]
        result = from_records(records, "region", "value")
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_named_tuples(self):
        from collections import namedtuple
        Row = namedtuple("Row", ["region", "value"])
        records = [Row("head", 10), Row("arm", 5)]
        result = from_records(records, "region", "value")
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_duck_typing_with_getitem(self):
        class FakeRow:
            def __init__(self, r, v):
                self._d = {"region": r, "value": v}
            def __getitem__(self, key):
                return self._d[key]
            def __getattr__(self, key):
                raise AttributeError(key)

        records = [FakeRow("trunk", 7.0)]
        result = from_records(records, "region", "value")
        self.assertEqual(result, [("trunk", 7.0)])


class TestFromCsv(unittest.TestCase):
    def test_parse_string(self):
        csv_data = "region,value\nhead,10\narm,5\n"
        result = from_csv(io.StringIO(csv_data), "region", "value")
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_custom_delimiter(self):
        csv_data = "region;value\nhead;10\narm;5\n"
        result = from_csv(io.StringIO(csv_data), "region", "value", delimiter=";")
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_file_like_object(self):
        csv_data = "reg,val\nleg,3.5\n"
        fh = io.StringIO(csv_data)
        result = from_csv(fh, "reg", "val")
        self.assertEqual(result, [("leg", 3.5)])


class TestFromJson(unittest.TestCase):
    def test_object_format(self):
        json_str = '{"head": 10, "arm": 5}'
        result = from_json(json_str)
        self.assertIn(("head", 10.0), result)
        self.assertIn(("arm", 5.0), result)

    def test_array_format(self):
        json_str = '[{"region": "head", "value": 10}, {"region": "arm", "value": 5}]'
        result = from_json(json_str, region_key="region", value_key="value")
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_file_like_object(self):
        import io
        json_str = '{"leg": 3}'
        fh = io.StringIO(json_str)
        result = from_json(fh)
        self.assertEqual(result, [("leg", 3.0)])


class TestAggregate(unittest.TestCase):
    def test_count(self):
        records = [("head",), ("arm",), ("head",), ("head",)]
        result = aggregate_count(records, region_index=0)
        self.assertEqual(result["head"], 3.0)
        self.assertEqual(result["arm"], 1.0)

    def test_count_stable_order(self):
        records = [("b",), ("a",), ("b",), ("c",)]
        result = aggregate_count(records)
        self.assertEqual(list(result.keys()), ["a", "b", "c"])

    def test_sum(self):
        records = [("head", 3.0), ("head", 7.0), ("arm", 5.0)]
        result = aggregate_sum(records)
        self.assertEqual(result["head"], 10.0)
        self.assertEqual(result["arm"], 5.0)

    def test_sum_stable_order(self):
        records = [("c", 1.0), ("a", 2.0), ("b", 3.0)]
        result = aggregate_sum(records)
        self.assertEqual(list(result.keys()), ["a", "b", "c"])

    def test_count_empty(self):
        self.assertEqual(aggregate_count([]), {})

    def test_sum_empty(self):
        self.assertEqual(aggregate_sum([]), {})


if __name__ == "__main__":
    unittest.main()
