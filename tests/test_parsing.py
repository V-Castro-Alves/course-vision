import unittest
from datetime import date
from unittest.mock import patch

from core.parsing import (
    ClassRow,
    assign_dates_to_classes,
    get_monday_of_week,
    normalize_classroom,
    normalize_row,
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

        # Test case 7: Name contains a hyphen but not a class code
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
        self.assertEqual(normalize_classroom("205 LAB"), "205/LAB")

        # Test with variations of separators
        self.assertEqual(normalize_classroom("LAB 302/SALA 101"), "LAB 302/SALA 101")
        self.assertEqual(normalize_classroom("LAB 302, SALA 101"), "LAB 302, SALA 101")
        self.assertEqual(normalize_classroom("LAB 302; SALA 101"), "LAB 302; SALA 101")

        # Test with "intelligent" splitting (number followed by space and room type)
        self.assertEqual(normalize_classroom("SALA 101 Sala"), "SALA 101/Sala")
        self.assertEqual(normalize_classroom("101 SALA"), "101/SALA")
        self.assertEqual(
            normalize_classroom("101SALA"), "101SALA"
        )  # Should not split as no space
        self.assertEqual(normalize_classroom("302 LAB."), "302/LAB.")
        self.assertEqual(normalize_classroom("205 ROOM"), "205/ROOM")
        self.assertEqual(normalize_classroom("302 LAB"), "302/LAB")
        self.assertEqual(
            normalize_classroom("302 LAB  "), "302/LAB"
        )  # With trailing spaces

        # Ensure existing splits are not affected by this new rule unless it matches the pattern
        self.assertEqual(normalize_classroom("LAB 302/SALA 101"), "LAB 302/SALA 101")
        self.assertEqual(normalize_classroom("Lab 302 Room 205"), "Lab 302 Room 205")

    def test_normalize_row(self):
        # Test case 1: Basic normalization
        row = ClassRow(
            class_code=" TES/II ",
            class_name=" Programacao Orientada a Objetos ",
            professor=" Dr. John Doe ",
            classroom=" LAB 302 ",
        )
        normalized = normalize_row(row)
        self.assertEqual(normalized.class_code, "TES/II")
        self.assertEqual(normalized.class_name, "Programacao Orientada a Objetos")
        self.assertEqual(normalized.professor, "Dr. John Doe")
        self.assertEqual(normalized.classroom, "LAB 302")

        # Test case 2: Professor extracted from class_name
        row = ClassRow(
            class_code="TES/II",
            class_name="Programacao Orientada a Objetos prof. Jane Smith",
            professor="",
            classroom="SALA 101",
        )
        normalized = normalize_row(row)
        self.assertEqual(normalized.class_code, "TES/II")
        self.assertEqual(normalized.class_name, "Programacao Orientada a Objetos")
        self.assertEqual(normalized.professor, "Jane Smith")
        self.assertEqual(normalized.classroom, "SALA 101")

        # Test case 3: Professor already present, should not extract from class_name
        row = ClassRow(
            class_code="TES/II",
            class_name="Programacao Orientada a Objetos prof. Jane Smith",
            professor="Dr. John Doe",
            classroom="SALA 101",
        )
        normalized = normalize_row(row)
        self.assertEqual(normalized.class_code, "TES/II")
        self.assertEqual(
            normalized.class_name, "Programacao Orientada a Objetos prof. Jane Smith"
        )  # Class name remains unchanged
        self.assertEqual(normalized.professor, "Dr. John Doe")
        self.assertEqual(normalized.classroom, "SALA 101")

        # Test case 4: Class name with class code prefix
        row = ClassRow(
            class_code="",
            class_name="MATH101 - Algebra",
            professor="Prof. Alan Turing",
            classroom="ROOM 200",
        )
        normalized = normalize_row(row)
        self.assertEqual(normalized.class_code, "MATH101")
        self.assertEqual(normalized.class_name, "Algebra")
        self.assertEqual(normalized.professor, "Prof. Alan Turing")
        self.assertEqual(normalized.classroom, "ROOM 200")

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

    def test_get_monday_of_week(self):
        # Test case 1: Today is Monday
        self.assertEqual(get_monday_of_week(date(2026, 3, 24)), date(2026, 3, 23))
        # Test case 2: Today is Wednesday
        self.assertEqual(get_monday_of_week(date(2026, 3, 26)), date(2026, 3, 23))
        # Test case 3: Today is Saturday (should return current week's Monday)
        self.assertEqual(get_monday_of_week(date(2026, 3, 29)), date(2026, 3, 23))
        # Test case 4: Today is Sunday (should return current week's Monday)
        self.assertEqual(get_monday_of_week(date(2026, 3, 30)), date(2026, 3, 30))

    def test_assign_dates_to_classes(self):
        # Sample classes
        class1 = ClassRow(class_code="C1", class_name="N1")
        class2 = ClassRow(class_code="C2", class_name="N2")
        class3 = ClassRow(class_code="C3", class_name="N3")
        class4 = ClassRow(class_code="C4", class_name="N4")
        class5 = ClassRow(class_code="C5", class_name="N5")
        class6 = ClassRow(class_code="C6", class_name="N6")

        # Assume today is Monday, 2026-03-24
        with patch("core.parsing.get_today_date", return_value=date(2026, 3, 24)):
            rows = [class1, class2, class3, class4, class5, class6]
            assigned_rows = assign_dates_to_classes(rows)

            # Monday
            self.assertEqual(assigned_rows[0].class_date, "2026-03-23")
            self.assertEqual(assigned_rows[0].day_index, 0)
            self.assertEqual(assigned_rows[0].start_time, "19:00")
            self.assertEqual(assigned_rows[0].end_time, "20:30")
            self.assertEqual(assigned_rows[1].class_date, "2026-03-23")
            self.assertEqual(assigned_rows[1].day_index, 0)
            self.assertEqual(assigned_rows[1].start_time, "20:50")
            self.assertEqual(assigned_rows[1].end_time, "22:30")

            # Tuesday
            self.assertEqual(assigned_rows[2].class_date, "2026-03-24")
            self.assertEqual(assigned_rows[2].day_index, 1)
            self.assertEqual(assigned_rows[2].start_time, "19:00")
            self.assertEqual(assigned_rows[2].end_time, "20:30")
            self.assertEqual(assigned_rows[3].class_date, "2026-03-24")
            self.assertEqual(assigned_rows[3].day_index, 1)
            self.assertEqual(assigned_rows[3].start_time, "20:50")
            self.assertEqual(assigned_rows[3].end_time, "22:30")

            # Wednesday
            self.assertEqual(assigned_rows[4].class_date, "2026-03-25")
            self.assertEqual(assigned_rows[4].day_index, 2)
            self.assertEqual(assigned_rows[4].start_time, "19:00")
            self.assertEqual(assigned_rows[4].end_time, "20:30")
            self.assertEqual(assigned_rows[5].class_date, "2026-03-25")
            self.assertEqual(assigned_rows[5].day_index, 2)
            self.assertEqual(assigned_rows[5].start_time, "20:50")
            self.assertEqual(assigned_rows[5].end_time, "22:30")

            self.assertEqual(len(assigned_rows), 6)

        # Test with fewer classes than days
        with patch("core.parsing.get_today_date", return_value=date(2026, 3, 24)):
            rows = [class1, class2]
            assigned_rows = assign_dates_to_classes(rows)

            # Monday
            self.assertEqual(assigned_rows[0].class_date, "2026-03-23")
            self.assertEqual(assigned_rows[0].day_index, 0)
            self.assertEqual(assigned_rows[1].class_date, "2026-03-23")
            self.assertEqual(assigned_rows[1].day_index, 0)

            self.assertEqual(len(assigned_rows), 2)

        # Test with more classes than available slots in the week (up to Friday)
        with patch("core.parsing.get_today_date", return_value=date(2026, 3, 24)):
            extra_classes = [
                ClassRow(class_code=f"EX{i}", class_name=f"EXN{i}") for i in range(15)
            ]
            rows = [class1, class2, class3, class4, class5, class6] + extra_classes
            assigned_rows = assign_dates_to_classes(rows)

            # Should only assign up to Friday (WEEKDAYS has 5 days, 2 classes per day = 10 classes)
            self.assertEqual(len(assigned_rows), 10)
            # Check last assigned day is Friday
            self.assertEqual(assigned_rows[9].class_date, "2026-03-27")
            self.assertEqual(assigned_rows[9].day_index, 4)


if __name__ == "__main__":
    unittest.main()
