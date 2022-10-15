import csv
from enum import IntEnum

def create_type_and_matchups():
    matchups = []
    type_names = []
    with open('type_matchup.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            single_type_matchup = list()
            first_col=True
            for col in row:
                if first_col:
                    type_names.append(col.strip())
                    first_col=False
                    continue
                single_type_matchup.append(int(col))
            matchups.append(single_type_matchup)
        print(type_names)
        print(matchups)
        Type = IntEnum('Type', {t:i for t,i in zip(type_names, range(len(type_names)))})
        print([t for t in Type])
        assert(Type.NULL in Type)
        assert(len(matchups) == len(matchups[0]))
    return Type, matchups

Type, EFFECTIVE_TABLE = create_type_and_matchups()
