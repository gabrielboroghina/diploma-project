from codecs import open

set = 'train'

out = open(f'data/ro_rrt-ud-{set}-.conllu', 'w', encoding="utf-8")

with open(f'data/ro_rrt-ud-{set}.conllu', 'r', encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if len(line.strip()) and line[0] != '#':
            tokens = line.split('\t')
            # print(tokens[7])
            if tokens[7] != "nsubj":
                tokens[7] = '-'
            lines[i] = '\t'.join(tokens)

    out.writelines(lines)
