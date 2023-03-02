"""Helper function for specific assertions."""


def assert_elements_type(elements, expected_type):
    """Ensure all elements in a collection match expected type."""
    assert all(isinstance(el, expected_type) for el in elements), [
        type(p) for p in elements
    ]
