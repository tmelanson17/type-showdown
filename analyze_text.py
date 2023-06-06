import csv
from type_matchup_reader import Type

typenames = [t.name for t in Type]

if __name__ == "__main__":
    txt_file = "output.txt"
    counts = {typ: 0 for typ in typenames}
    total=0
    with open(txt_file, 'r') as fp:
        txt = fp.read()
        for typename in typenames:
            counts[typename] = txt.count(typename)
            total += counts[typename]
    print("Percentage of each type:")
    for typename in typenames:
        print(f"{typename}: {counts[typename]/total:0.2f}")


