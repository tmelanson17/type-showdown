import csv
from enum import IntEnum

def create_type_and_matchups():
    matchups = []
    type_names = []
    with open('type_matchup.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        first_row=True
        for i, row in enumerate(csv_reader):
            if first_row:
                for typename in row[1:]:
                    type_names.append(typename)
                first_row=False
                continue

            single_type_matchup = list()
            first_col=True
            for col in row:
                if first_col:
                    assert i <= len(type_names) and col == type_names[i-1], "Type matchup rows/columns must match!"
                    first_col=False
                    continue
                single_type_matchup.append(int(col))
            matchups.append(tuple(single_type_matchup))
        print(type_names)
        print(matchups)
        Type = IntEnum('Type', {t:i for t,i in zip(type_names, range(len(type_names)))})
        print([t for t in Type])
        assert Type.NULL in Type, "Must include NULL Type!"
        assert len(matchups) == len(matchups[0]), "Type matchup rows/columns must match!"
    return Type, tuple(m for m in matchups)

Type, EFFECTIVE_TABLE = create_type_and_matchups()
