from unittest import TestCase

from src.utils import ChangesAreNotEmptyMixin


class TestChangeAreNotEmptyMixin(TestCase):

    def test_changes_are_empty(self) -> None:
        with self.assertRaises(ValueError):
            ChangesAreNotEmptyMixin.changes_are_not_empty({})

    def test_changes_are_not_empty(self) -> None:
        expected_result = {'field': 'value'}
        result = ChangesAreNotEmptyMixin.changes_are_not_empty({'field': 'value'})
        self.assertEqual(result, expected_result)
