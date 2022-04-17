def get_key_from_value(dict, str_to_find):
    """
    :param dict: dictionnary dict[key] = values
    :param str_to_find: occurence to find in the values for each key (* can be used)
    :return: the key where occurence is found in one of the values
    """
    output = []
    for key in dict.keys():
        for value in dict[key]:
            add_key = False
            if value.startswith("*") and value.endswith("*") and value[1:-1] in str_to_find:
                add_key = True
            elif value.startswith("*") and str_to_find.endswith(value[1:]):
                add_key = True
            elif value.endswith("*") and str_to_find.startswith(value[:-1]):
                add_key = True
            elif value == str_to_find:
                add_key = True
            if add_key and key not in output:
                output.append(key.capitalize().replace("_", " "))
    return output
