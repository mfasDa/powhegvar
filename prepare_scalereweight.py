#! /usr/bin/env python3

import argparse

def replace_value(input: str, newvalue: str):
    command = input
    if "!" in command:
        command = command[:command.find("!")-1]
    if "#" in command:
        command = command[:command.find("#")-1]
    tokens = command.split(" ")
    stripped_tokens = []
    for tok in tokens:
        if len(tok):
            stripped_tokens.append(tok)
    oldvalue = stripped_tokens[1]
    print(f"Replaceing {oldvalue} with {newvalue}")
    output = input.replace(oldvalue, newvalue)
    print(f"New line: {output}")
    return output
                    


def process_input(inputfile: str, outputfile: str, muf: float, mur: float, weightID: int):
    print("Parameters for reweighted POWHEG input:")
    print("----------------------------------------------------------------------------------")
    print(f"INPUT:        {inputfile}".format(inputfile))
    print(f"OUTPUT:       {outputfile}")
    print(f"MUF:          {muf:.1f}")
    print(f"MUR:          {mur:.1f}")
    print(f"ID:           {weightID}")
    print("----------------------------------------------------------------------------------")
    with open(inputfile, "r") as reader:
        with open(outputfile,  "w") as writer:
            weightidset = False
            weightdescset = False
            weightgroupset = False
            for line in reader:
                if line.startswith("!") or line.startswith("#"):
                    writer.write("{}\n".format(line.rstrip("\n")))
                elif "storeinfo_rwgt" in line:
                    # drop storeinfo_rwgt in reweight mode
                    continue
                elif "renscfact" in line:
                    newline = replace_value(line.rstrip("\n"), f"{mur:.1f}")
                    writer.write("{}\n".format(newline))
                elif "facscfact" in line:
                    newline = replace_value(line.rstrip("\n"), f"{muf:.1f}")
                    writer.write("{}\n".format(newline))
                elif "lhrwgt_id" in line:
                    newline = replace_value(line.rstrip("\n"), f"\'{weightID}\'")
                    writer.write("{}\n".format(newline))
                    weightidset = True
                elif "lhrwgt_descr" in line:
                    newline = replace_value(line.rstrip("\n"), f"\'muf={muf:.1f}, mur={mur:.1f}\'")
                    writer.write("{}\n".format(newline))
                    weightdescset = True
                elif "lhrwgt_group_name" in line:
                    newline = replace_value(line.rstrip("\n"), "\'scale uncertainties\'")
                    writer.write("{}\n".format(newline))
                    weightgroupset = True
                else:
                    writer.write("{}\n".format(line.rstrip("\n")))
            writer.write("compute_rwgt 1\n")
            if not weightidset:
                writer.write("lhrwgt_id \'{}\'\n".format(weightID))
            if not weightdescset:
                writer.write("lhrwgt_descr \'muf={:.1f}, mur={:.1f}\'\n".format(muf, mur))
            if not weightgroupset:
                writer.write("lhrwgt_group_name \'scale uncertainties\'\n")
            writer.write("lhrwgt_group_combine \'foo\'\n")
            writer.close()
        reader.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("prepare_scalereweight.py")
    parser.add_argument("inputfile", metavar="INPUTFILE", type=str, help="Input configuration file")
    parser.add_argument("outputfile", metavar="OUTPUTFILE", type=str, help="Output configuration file")
    parser.add_argument("muf", metavar="MUF", type=float, help="Factorisation scale")
    parser.add_argument("mur", metavar="MUR", type=float, help="Renormalisation scale")
    parser.add_argument("weightid", metavar="WEIGHTID", type=int, help="Weight ID")
    args = parser.parse_args()
    process_input(args.inputfile, args.outputfile, args.muf, args.mur, args.weightid)