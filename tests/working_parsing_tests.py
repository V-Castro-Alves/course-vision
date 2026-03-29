import unittest

from core.parsing import (
    ClassRow,
    normalize_classroom,
    should_skip_row,
    split_class_code_and_name,
)


class TestParsingFunctions(unittest.TestCase):
    def test_split_class_code_and_name(self):
        # Test case 1: Code and name are separate
        code, name = split_class_code_and_name(
            "TES/II", "Programacao Orientada a Objetos"
        )
        self.assertEqual(code, "TES/II")
        self.assertEqual(name, "Programacao Orientada a Objetos")

        # Test case 2: Name contains code prefix
        code, name = split_class_code_and_name(
            "", "TES/II-Programacao Orientada a Objetos"
        )
        self.assertEqual(code, "TES/II")
        self.assertEqual(name, "Programacao Orientada a Objetos")

        # Test case 3: Name contains code prefix with extra space/hyphen
        code, name = split_class_code_and_name(
            "", "TES/II - Programacao Orientada a Objetos"
        )
        self.assertEqual(code, "TES/II")
        self.assertEqual(name, "Programacao Orientada a Objetos")

        # Test case 4: Code and name are empty
        code, name = split_class_code_and_name("", "")
        self.assertEqual(code, "")
        self.assertEqual(name, "")

        # Test case 5: Only code is provided
        code, name = split_class_code_and_name("TES/II", "")
        self.assertEqual(code, "TES/II")
        self.assertEqual(name, "")

        # Test case 6: Only name is provided, no detectable code
        code, name = split_class_code_and_name("", "Programacao Orientada a Objetos")
        self.assertEqual(code, "")
        self.assertEqual(name, "Programacao Orientada a Objetos")

        # Test case 7: Name contains a hyphen but not a class code (new looks_like_class_code should handle this)
        code, name = split_class_code_and_name("", "Some-Name-With-Hyphens")
        self.assertEqual(code, "")
        self.assertEqual(name, "Some-Name-With-Hyphens")

    def test_normalize_classroom(self):
        self.assertEqual(normalize_classroom("LAB 302"), "LAB 302")
        self.assertEqual(normalize_classroom("SALA 101"), "SALA 101")
        self.assertEqual(normalize_classroom("LAB. 302"), "LAB. 302")
        self.assertEqual(normalize_classroom("ROOM 205"), "ROOM 205")
        self.assertEqual(normalize_classroom("Online"), "Online")
        self.assertEqual(normalize_classroom(""), "")
        self.assertEqual(normalize_classroom("  LAB 302  "), "LAB 302")
        self.assertEqual(normalize_classroom("Sala 101"), "Sala 101")
        self.assertEqual(
            normalize_classroom("205 LAB"), "205/LAB"
        )  # Number followed by room type

        # Test with variations of separators already present
        self.assertEqual(normalize_classroom("LAB 302/SALA 101"), "LAB 302/SALA 101")
        self.assertEqual(normalize_classroom("LAB 302, SALA 101"), "LAB 302, SALA 101")
        self.assertEqual(normalize_classroom("LAB 302; SALA 101"), "LAB 302; SALA 101")

        # Test with "intelligent" splitting (digit followed by space and room type)
        self.assertEqual(normalize_classroom("SALA 101 Sala"), "SALA 101/Sala")
        self.assertEqual(normalize_classroom("101 SALA"), "101/SALA")
        self.assertEqual(
            normalize_classroom("101SALA"), "101SALA"
        )  # No space, should not split
        self.assertEqual(normalize_classroom("302 LAB."), "302/LAB.")
        self.assertEqual(normalize_classroom("205 ROOM"), "205/ROOM")
        self.assertEqual(normalize_classroom("302 LAB"), "302/LAB")
        self.assertEqual(
            normalize_classroom("302 LAB  "), "302/LAB"
        )  # With trailing spaces

        # Ensure multi-part room names are also split if they follow the pattern
        self.assertEqual(normalize_classroom("Lab 302 Room 205"), "Lab 302/Room 205")

    def test_should_skip_row(self):
        # Test case 1: Empty row
        row = ClassRow()
        self.assertTrue(should_skip_row(row))

        # Test case 2: Row with only class code (but invalid for class)
        row = ClassRow(class_code="codigo")
        self.assertTrue(should_skip_row(row))

        # Test case 3: Row with semester text
        row = ClassRow(class_name="5o Semestre")
        self.assertTrue(should_skip_row(row))

        # Test case 4: Valid row
        row = ClassRow(
            class_code="TES/II",
            class_name="POO",
            professor="John Doe",
            classroom="LAB 302",
        )
        self.assertFalse(should_skip_row(row))

        # Test case 5: Valid row with only class_name
        row = ClassRow(class_name="Introduction to Python")
        self.assertFalse(should_skip_row(row))

        # Test case 6: Valid row with only professor
        row = ClassRow(professor="Jane Smith")
        self.assertFalse(should_skip_row(row))

        # Test case 7: Valid row with only classroom
        row = ClassRow(classroom="SALA 101")
        self.assertFalse(should_skip_row(row))

        # Test case 8: Class name is a common header word
        row = ClassRow(class_name="disciplina")
        self.assertTrue(should_skip_row(row))

        # Test case 9: Professor is a common header word
        row = ClassRow(professor="professor")
        self.assertTrue(should_skip_row(row))

        # Test case 10: No professor, classroom is a common header word
        row = ClassRow(classroom="sala")
        self.assertTrue(should_skip_row(row))


if __name__ == "__main__":
    unittest.main()
