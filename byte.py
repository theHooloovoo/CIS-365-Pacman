with open("atma_final_bots.py") as fp:
    for i, line in enumerate(fp):
        if "\xe2" in line:
            print i, repr(line)