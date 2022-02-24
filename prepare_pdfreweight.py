#! /usr/bin/env python3

import sys

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
    print("Replaceing {} with {}".format(oldvalue, newvalue))
    output = input.replace(oldvalue, newvalue)
    print("New line: {}".format(output))
    return output
                    


def process_input(inputfile: str, outputfile: str, pdfset: int, weightID: int):
    print("Parameters for reweighted POWHEG input:")
    print("----------------------------------------------------------------------------------")
    print("INPUT:        {}".format(inputfile))
    print("OUTPUT:       {}".format(outputfile))
    print("PDFSET:       {}".format(pdfset))
    print("ID:           {}".format(weightID))
    print("----------------------------------------------------------------------------------")
    with open(inputfile, "r") as reader:
        with open(outputfile,  "w") as writer:
            weightidset = False
            weightdescset = False
            weightgroupset = False
            for line in reader:
                if line.startswith("!") or line.startswith("#"):
                    writer.write("{}\n".format(line.rstrip("\n")))
                elif "lhans" in line:
                    newline = replace_value(line.rstrip("\n"), "{}".format(pdfset))
                    writer.write("{}\n".format(newline))
                elif "lhrwgt_id" in line:
                    newline = replace_value(line.rstrip("\n"), "\'{}\'".format(weightID))
                    writer.write("{}\n".format(newline))
                    weightidset = True
                elif "lhrwgt_descr" in line:
                    newline = replace_value(line.rstrip("\n"), "\'pdf {}\'".format(pdfset))
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
                writer.write("lhrwgt_id \'{}\'\n".format(weightID))
            if not weightdescset:
                writer.write("lhrwgt_descr \'pdf {}\'\n".format(pdfset))
            if not weightgroupset:
                writer.write("lhrwgt_group_name \'pdf uncertainties\'\n")
            writer.write("lhrwgt_group_combine \'foo\'\n")
            writer.close()
        reader.close()

if __name__ == "__main__":
    process_input(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])