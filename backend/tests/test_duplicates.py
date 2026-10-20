from app.constants import Label, Laterality, Split
from app.models import ExamRecord
from ingest.duplicates import mark_duplicates
from tests.factories import make_exam

PROFILE = [476.0, 487.0, 520.0, 574.0]


def exam(
    case: int,
    thickness: list[float],
    label: Label = "suspect",
    split: Split = "train_validation",
    laterality: Laterality = "OD",
) -> ExamRecord:
    return make_exam(
        split=split, label=label, case=case, thickness=thickness, laterality=laterality
    )


def test_identical_profiles_with_same_label_keep_one() -> None:
    first, second = exam(3, PROFILE), exam(7, PROFILE)
    mark_duplicates([first, second])
    assert first.possible_duplicate_of == [second.exam_id]
    assert second.possible_duplicate_of == [first.exam_id]
    assert (first.stats_excluded, first.stats_exclusion_reason) == (False, None)
    assert (second.stats_excluded, second.stats_exclusion_reason) == (True, "duplicate")


def test_keeper_prefers_train_split_then_lowest_case() -> None:
    test_exam = exam(1, PROFILE, split="independent_test")
    train_high = exam(9, PROFILE)
    train_low = exam(2, PROFILE)
    mark_duplicates([test_exam, train_high, train_low])
    assert [e.stats_excluded for e in (test_exam, train_high, train_low)] == [True, True, False]


def test_conflicting_labels_exclude_every_member() -> None:
    kcn, suspect = exam(3, PROFILE, label="keratoconus"), exam(7, PROFILE, label="suspect")
    mark_duplicates([kcn, suspect])
    for member in (kcn, suspect):
        assert member.stats_excluded
        assert member.stats_exclusion_reason == "duplicate_conflicting_labels"


def test_three_member_group_is_linked_transitively() -> None:
    a = exam(1, [500.0, 510.0, 520.0, 530.0, 540.0])
    b = exam(2, [500.0, 510.0, 520.0, 530.0, 560.0])
    c = exam(3, [510.0, 520.0, 530.0, 560.0, 600.0])
    mark_duplicates([a, b, c])
    assert a.possible_duplicate_of == sorted([b.exam_id, c.exam_id])
    assert c.possible_duplicate_of == sorted([a.exam_id, b.exam_id])
    assert sum(not e.stats_excluded for e in (a, b, c)) == 1


def test_fewer_than_four_values_never_match() -> None:
    first, second = exam(1, [476.0, 487.0, 520.0]), exam(2, [476.0, 487.0, 520.0])
    mark_duplicates([first, second])
    assert first.possible_duplicate_of == []
    assert not first.stats_excluded and not second.stats_excluded


def test_low_overlap_is_not_a_duplicate() -> None:
    first = exam(1, [500.0, 510.0, 520.0, 530.0, 540.0, 550.0, 560.0])
    second = exam(2, [500.0, 510.0, 520.0, 530.0, 640.0, 650.0, 660.0])
    mark_duplicates([first, second])
    assert first.possible_duplicate_of == []


def test_contradicting_laterality_is_not_a_duplicate() -> None:
    first, second = exam(1, PROFILE, laterality="OD"), exam(2, PROFILE, laterality="OS")
    mark_duplicates([first, second])
    assert first.possible_duplicate_of == []


def test_unknown_laterality_still_matches() -> None:
    first, second = exam(1, PROFILE, laterality="unknown"), exam(2, PROFILE, laterality="OS")
    mark_duplicates([first, second])
    assert first.possible_duplicate_of == [second.exam_id]


def test_unrelated_exams_are_untouched() -> None:
    first, second = exam(1, PROFILE), exam(2, [431.0, 454.0, 511.0, 570.0])
    mark_duplicates([first, second])
    assert first.possible_duplicate_of == second.possible_duplicate_of == []
