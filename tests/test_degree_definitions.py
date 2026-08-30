from calculations.degree_definitions import (
    degree_key,
    load_la_volasfera,
    lookup_la_volasfera,
)


def test_la_volasfera_contains_all_360_degrees():
    assert len(load_la_volasfera()) == 360


def test_position_minutes_are_removed_for_degree_lookup():
    assert degree_key("10CP20") == "10CP"


def test_la_volasfera_entry_has_image_and_interpretation():
    definition = lookup_la_volasfera("0AR15")

    assert definition.title == "Degree of Strength and Passion"
    assert definition.image.startswith("A strong man standing")
    assert definition.interpretation.startswith("It denotes a man capable")
