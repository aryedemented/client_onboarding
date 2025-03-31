from typing import Dict, List


def update_field(list_of_dicts: List[Dict]):
    for idx, elem in enumerate(list_of_dicts):


if __name__ == '__main__':
    # TODO: Move this to tests
    orig_dict = {
        'edges':
             [
                 {"from": "all-purpose flour", "instructions": "some text", "to": "batter"},
                 {"from": "sugar", "instructions": "sugar text", "to": "batter"},
             ],
        'ingredients':
            [
                {"name": "all-purpose flour", "quantity": "2 cups", "remarks": "floor remark text"},
                {"name": "sugar", "quantity": "2 tbsp", "remarks": "sugar remark text"},
            ],
        'resources':
            [
                {"remarks": "oven remark text", "name": "oven", "usage_time": "10 min"},
                {"name": "bowl", "usage_time": "4 min", "remarks": "bowl remark text"},
                {"name": "mixer", "usage_time": "4 min", "remarks": "mixer remark text"},
            ],
         }

    fine_tune_dict = {
        'edges':
             [
                 {"instructions": "SOME_TEXT", "to": "BATTER"},
             ],
        'ingredients':
            [
                {"name": "all-purpose flour", "quantity": "3 CUPS", "remarks": "FLOOR REMARK TEXT"},
                {"name": "SUGAR", "quantity": "2 tbsp", "remarks": "sugar remark text"},
            ]
         }

    merged = merge_dicts(orig_dict, fine_tune_dict)
    print(f"orig:   {orig_dict}")
    print(f"merged: {merged}")
    print(f"added:  {fine_tune_dict}")
