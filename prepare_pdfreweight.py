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
                    


def process_input(inputfile: str, outputfile: str, pdfset: int, weightID: int):
    print("Parameters for reweighted POWHEG input:")
    print("----------------------------------------------------------------------------------")
    print(f"INPUT:        {inputfile}")
    print(f"OUTPUT:       {outputfile}")
    print(f"PDFSET:       {pdfset}")
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
                elif "lhans" in line:
                    newline = replace_value(line.rstrip("\n"), f"{pdfset}")
                    writer.write("{}\n".format(newline))
                elif "lhrwgt_id" in line:
                    newline = replace_value(line.rstrip("\n"), f"\'{weightID}\'")
                    writer.write("{}\n".format(newline))
                    weightidset = True
                elif "lhrwgt_descr" in line:
                    newline = replace_value(line.rstrip("\n"), f"\'pdf {pdfset}\'")
                    writer.write("{}\n".format(newline))
                    weightdescset = True
                elif "lhrwgt_group_name" in line:
                    newline = replace_value(line.rstrip("\n"), "\'pdf uncertainties\'")
                    writer.write("{}\n".format(newline))
                    weightgroupset = True
                else:
                    writer.write("{}\n".format(line.rstrip("\n")))
            writer.write("compute_rwgt 1\n")
            if not weightidset:
                writer.write(f"lhrwgt_id \'{weightID}\'\n")
            if not weightdescset:
                writer.write(f"lhrwgt_descr f\'pdf {pdfset}\'\n")
            if not weightgroupset:
                writer.write("lhrwgt_group_name \'pdf uncertainties\'\n")
            writer.write("lhrwgt_group_combine \'foo\'\n")
            writer.close()
        reader.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("prepare_scalereweight.py")
    parser.add_argument("inputfile", metavar="INPUTFILE", type=str, help="Input configuration file")
    parser.add_argument("outputfile", metavar="OUTPUTFILE", type=str, help="Output configuration file")
    parser.add_argument("pdfset", metavar="PDFSET", type=int, help="PDF set")
    parser.add_argument("weightid", metavar="WEIGHTID", type=int, help="Weight ID")
    args = parser.parse_args()
    process_input(args.inputfile, args.outputfile, args.pdfset, args.weightid)