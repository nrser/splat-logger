from typing import Union

# SEE https://docs.python.org/3.10/library/json.html#json.JSONEncoder
JSONEncodable = Union[
    dict,
    list,
    tuple,
    str,
    int,
    float,
    bool,
    None,
]