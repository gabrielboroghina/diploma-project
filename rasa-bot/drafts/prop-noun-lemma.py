from codecs import open

out = open('../data/lookups/prop-noun-lemmas.json', 'w', encoding="utf-8")

out.write("{\n")

with open('data/subst-proprii', 'r', encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line.endswith("a"):
            if line == "Andreea":
                out.write(f'"{line[:-1]}i": "{line}",\n'.lower())
            elif line[-2] in ['c', 'k', 'g']:
                out.write(f'"{line[:-1]}ăi": "{line}",\n'.lower())
            else:
                out.write(f'"{line[:-1]}ei": "{line}",\n'.lower())

out.write("}\n")
