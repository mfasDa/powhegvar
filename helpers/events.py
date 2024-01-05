#! /usr/bin/env python3

from helpers.powhegconfig import replace_value

def create_config_nevens(inputfile: str, outputfile: str, nevents: int):
    print("Parameters for reweighted POWHEG input:")
    print("----------------------------------------------------------------------------------")
    print(f"INPUT:                  {inputfile}")
    print(f"OUTPUT:                 {outputfile}")
    print(f"Number of events:       {nevents}")
    print("----------------------------------------------------------------------------------")
    key_nevents = "numevts"
    with open(inputfile, "r") as reader:
        with open(outputfile,  "w") as writer:
            for line in reader:
                if line.startswith(key_nevents):
                    newline = replace_value(line.rstrip("\n"), f"{nevents}")
                    writer.write("{}\n".format(newline))
                else:
                    writer.write("{}\n".format(line.rstrip("\n")))
            writer.close()
        reader.close()