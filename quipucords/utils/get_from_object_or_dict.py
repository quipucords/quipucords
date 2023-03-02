"""get_from_object_or_dict module."""


def get_from_object_or_dict(instance, dict_obj, key):
    """Get an attribute from instance or key from dictionary - in this order."""
    return getattr(instance, key, None) or dict_obj.get(key)
