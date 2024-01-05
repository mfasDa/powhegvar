#! /usr/bin/env python3

import logging

from helpers.powhegconfig import replace_value

class weightID:

    def __init__(self, name: str = "", title: str = ""):
        self.__name = name
        self.__title = title

    def __eq__(self, other) -> bool:
        if isinstance(other, weightID):
            return self.__name == other.name and self.__title == other.__title
        return False

    def get_name(self) -> str:
        return self.__name
    
    def get_title(self) -> str:
        return self.__title

    def set_name(self, name: str):
        self.__name = name

    def set_title(self, title: str):
        self.__title = title

    name = property(fget=get_name, fset=set_name)
    title = property(fget=get_title, fset=set_title)



def create_config_pdfreweight(inputfile: str, outputfile: str, pdfset: int, currentid: int):
    logging.info("Parameters for reweighted POWHEG input:")
    logging.info("----------------------------------------------------------------------------------")
    logging.info("INPUT:        %s", inputfile)
    logging.info("OUTPUT:       %s", outputfile)
    logging.info("PDFSET:       %s", pdfset)
    logging.info("ID:           %s", currentid)
    logging.info("----------------------------------------------------------------------------------")
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
                    newline = replace_value(line.rstrip("\n"), f"\'{currentid}\'")
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
                writer.write(f"lhrwgt_id \'{currentid}\'\n")
            if not weightdescset:
                writer.write(f"lhrwgt_descr f\'pdf {pdfset}\'\n")
            if not weightgroupset:
                writer.write("lhrwgt_group_name \'pdf uncertainties\'\n")
            writer.write("lhrwgt_group_combine \'foo\'\n")
            writer.close()
        reader.close()

def create_config_scalereweight(inputfile: str, outputfile: str, muf: float, mur: float, currentid: int):
    logging.info("Parameters for reweighted POWHEG input:")
    logging.info("----------------------------------------------------------------------------------")
    logging.info("INPUT:        %s", inputfile)
    logging.info("OUTPUT:       %s", outputfile)
    logging.info("MUF:          %.1f", muf)
    logging.info("MUR:          %.1f", mur)
    logging.info("ID:           %d", currentid)
    logging.info("----------------------------------------------------------------------------------")
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
                    newline = replace_value(line.rstrip("\n"), f"\'{currentid}\'")
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
                writer.write("lhrwgt_id \'{}\'\n".format(currentid))
            if not weightdescset:
                writer.write("lhrwgt_descr \'muf={:.1f}, mur={:.1f}\'\n".format(muf, mur))
            if not weightgroupset:
                writer.write("lhrwgt_group_name \'scale uncertainties\'\n")
            writer.write("lhrwgt_group_combine \'foo\'\n")
            writer.close()
        reader.close()
                

def build_weightID_pdfreweight(pdfset: int, currentid: int) -> weightID:
    return weightID(f"{currentid}", f"pdf {pdfset}")

def build_weightID_scalereweight(muf: float, mur: float, currentid: int) -> weightID:
    return weightID(f"{currentid}", f"muf={muf:.1f}, mur={mur:.1f}")