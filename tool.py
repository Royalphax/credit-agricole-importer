def get_key_from_value(dict, str_to_check):
    """
    :param dict: dictionnary dict[key] = values
    :param str_to_check: occurence to find in the values for each key (* can be used)
    :return: the key where occurence is found in one of the values
    """
    output = []
    for key in dict.keys():
        for value in dict[key]:
            if is_equal(value, str_to_check) and key not in output:
                output.append(key.title().replace("_", " "))
    return output


def is_in_list(list_to_check, str_to_check):
    """
    :param value: Value to find in str_to_check
    :param list_to_check: List of string to check
    :return: if value is found in str_to_check
    """
    for elem in list_to_check:
        if is_equal(elem, str_to_check):
            return True
    return False


def is_equal(value, str_to_check):
    """
    :param value: Value to find in str_to_check
    :param str_to_check: String in which we check
    :return: if value is found in str_to_check using star indicators
    """
    output = False
    value = value.upper()
    str_to_check = str_to_check.upper()
    if value.startswith("*") and value.endswith("*") and value[1:-1] in str_to_check:
        output = True
    elif value.startswith("*") and str_to_check.endswith(value[1:]):
        output = True
    elif value.endswith("*") and str_to_check.startswith(value[:-1]):
        output = True
    elif value == str_to_check:
        output = True
    return output


def convert_time(seconds):
    def pluralize(unit, name, is_seconds=False):
        unit_rounded = round(unit, 1) if is_seconds else unit
        if unit_rounded == 1:
            return f"{unit_rounded} {name}"
        else:
            return f"{unit_rounded} {name}s"

    seconds_rounded = round(seconds, 1)
    if seconds_rounded < 60:
        return pluralize(seconds_rounded, "second", True)
    elif seconds_rounded < 3600:
        minutes, seconds = divmod(seconds_rounded, 60)
        return f"{pluralize(minutes, 'minute')}, {pluralize(seconds, 'second', True)}"
    else:
        hours, remainder = divmod(seconds_rounded, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{pluralize(hours, 'hour')}, {pluralize(minutes, 'minute')}, {pluralize(seconds, 'second', True)}"