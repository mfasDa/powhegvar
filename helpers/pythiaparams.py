#! /usr/bin/env python3

import argparse
import logging
import os

class InitializedValue(object):

    def __init__(self):
        self.__value = None

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    def is_initialised(self):
        return self.__value != None

class PythiaParams(object):

    def __init__(self):
        self.__tune = InitializedValue()
        self.__pdfset = InitializedValue()
        self.__mpi = InitializedValue()
        self.__decay = InitializedValue()
        self.__ptcut = InitializedValue()
        self.__ptcutcharged = InitializedValue()
        self.__ptcutneutral =InitializedValue()
        self.__ecut = InitializedValue()
        self.__ecutcharged =InitializedValue()
        self.__ecutneutral = InitializedValue()
        self.__jettype = InitializedValue()
        self.__recombinationScheme = InitializedValue()
        self.__yboost = InitializedValue()

    def set_tune(self, tune: int):
        if tune >= 0 and tune <=32:
            self.__tune.value = tune
        else:
            logging.error("Tune %d not implemented in PYTHIA")
        
    def set_pdf(self, pdfset: int):
        if pdfset > 0:
            self.__pdfset.value = pdfset
        else:
            logging.error("PDF set cannot be negative")

    def set_mpi(self, mpi: bool):
        self.__mpi.value = mpi

    def set_decay(self, decay: bool):
        self.__decay.value = decay

    def set_ptecut(self, ptcut: float, energy: bool, all: bool = True, charged: bool = True):
        if ptcut < 0:
            logging.error("pt/energy cut cannot be negative")
            return
        if energy:
            if all:
                self.__ecut.value = ptcut
            elif charged:
                self.__ecutcharged.value = ptcut
            else:
                self.__ecutneutral = ptcut
        else:
            if all:
                self.__ptcut.value = ptcut
            elif charged:
                self.__ptcutcharged.value = ptcut
            else:
                self.__ptcutneutral = ptcut

    def set_yboost(self, yboost: float):
        self.__yboost.value = yboost
    
    def set_jettype(self, jettype: str):
        jettypes = ["full", "charged"]
        if not jettype in jettypes:
            logging.error("Jet type %s not supported", jettype)
            return
        self.__jettype.value = jettype

    def set_recombinationscheme(self, recombinationscheme: str):
        supported_schemes = ["Escheme", "ptscheme", "pt2scheme", "Etscheme",  "Et2scheme"]
        if not recombinationscheme in supported_schemes:
            logging.error("Recombination scheme %s not supported", recombinationscheme)
            return
        self.__recombinationScheme.value = recombinationscheme

    def export_environment(self):
        if self.__tune.is_initialised():
            os.environ["CONFIG_TUNE"] = f"{self.__tune.value}"
        if self.__pdfset.is_initialised():
            os.environ["CONFIG_PDFSET"] = f"{self.__pdfset.value}"
        if self.__mpi.is_initialised():
            os.environ["CONFIG_MPI"] = "{}".format(1 if self.__mpi.value else 0)
        if self.__decay.is_initialised():
            os.environ["CONFIG_DECAY"] = "{}".format(1 if self.__mpi.value else 0)
        if self.__yboost.is_initialised():
            os.environ["CONFIG_YBOOST"] = "{}".format(int(self.__yboost.value * 1000.))
        if self.__ptcut.is_initialised():
            self.__export_energycut("PTCUT", self.__ptcut.value)
        if self.__ptcutcharged.is_initialised():
            self.__export_energycut("CHPTCUT", self.__ptcutcharged.value)
        if self.__ptcutneutral.is_initialised():
            self.__export_energycut("NEPTCUT", self.__ptcutneutral.value)
        if self.__ecut.is_initialised():
            self.__export_energycut("ECUT", self.__ecut.value)
        if self.__ecutcharged.is_initialised():
            self.__export_energycut("CHECUT", self.__ecutcharged.value)
        if self.__ecutneutral.is_initialised():
            self.__export_energycut("NEECUT", self.__ecutneutral.value)
        if self.__jettype.is_initialised():
            os.environ["CONFIG_JETTYPE"] = "{}".format(1 if self.__jettype.value == "full" else 0)
        if self.__recombinationScheme.is_initialised():
            os.environ["CONFIG_RECOMBINATIONSCHEME"] = self.__recombinationScheme.value

    def __export_energycut(self, name: str, value: float):
        os.environ[f"CONFIG_{name}"] = "{}".format(int(value*1000.))

    def serialize(self) -> str:
        def add_optional_separator(data: str):
            newdata = data
            if len(newdata):
                newdata += ":"
            return newdata

        serialized = ""
        if self.__tune.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized +=  f"tune={self.__tune.value}"
        if self.__pdfset.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += f"pdfset={self.__pdfset.value}"
        if self.__mpi.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "mpi={}".format("true" if self.__mpi.value else "false")
        if self.__decay.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "decays={}".format("true" if self.__mpi.value else "false")
        if self.__yboost.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "yboost={:.3f}".format(self.__yboost.value)
        if self.__ptcut.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "ptmin={:.3f}".format(self.__ptcut.value)
        if self.__ptcutcharged.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "ptmincharged={:.3f}".format(self.__ptcutcharged.value)
        if self.__ptcutneutral.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "ptminneutral={:.3f}".format(self.__ptcutneutral.value)
        if self.__ecut.is_initialised():
            serialized =  add_optional_separator(serialized)
            serialized += "emin={:.3f}".format(self.__ecut.value)
        if self.__ecutcharged.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "emincharged={:.3f}".format(self.__ecutcharged.value)
        if self.__ecutneutral.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += "eminneutral={:.3f}".format(self.__ecutneutral.value)
        if self.__jettype.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += f"jettype={self.__jettype.value}"
        if self.__recombinationScheme.is_initialised():
            serialized = add_optional_separator(serialized)
            serialized += f"recombinationScheme={self.__recombinationScheme.value}"
        return serialized

    def deserialize(self, settings: str):
        for entry in settings.split(":"):
            tokens = entry.split("=")
            key = tokens[0]
            value = tokens[1]
            if key == "tune":
                self.set_tune(int(value))
                continue
            if key == "pdfset":
                self.set_pdf(int(value))
                continue
            if key == "mpi":
                self.set_mpi(True if value == "true" else False)
                continue
            if key == "decays":
                self.set_decay(True if value == "true" else False)
                continue
            if key == "yboost":
                self.set_yboost(float(value))
                continue
            if key == "ptmin":
                self.set_ptecut(float(value), False, True, False)
                continue
            if key == "ptmincharged":
                self.set_ptecut(float(value), False, False, True)
                continue
            if key == "ptminneutral":
                self.set_ptecut(float(value), False, False, False)
                continue
            if key == "emin":
                self.set_ptecut(float(value), True, True, False)
                continue
            if key == "emincharged":
                self.set_ptecut(float(value), True, False, True)
                continue
            if key == "eminneutral":
                self.set_ptecut(float(value), True, False, False)
                continue
            if key == "jettype":
                self.set_jettype(value)
                continue
            if key == "recombinationScheme":
                self.set_recombinationscheme(value)
                continue
            logging.error("Unsupported key: %s", key)

    def define_args(self, args: argparse.ArgumentParser):
        args.add_argument("--tune", metavar="TUNE", type=int, default=-1, help="PYTHIA tune")
        args.add_argument("--pdfset", metavar="PDFSET", type=int, default=-1, help="PDF set")
        args.add_argument("--with_mpi", action="store_true", help="Enable MPI in PYTHIA")
        args.add_argument("--no_decay", action="store_true", help="Disable decays of long-lived particles in PYTHIA")
        args.add_argument("--jettype", metavar="JETTYPE", type=str, default="full", help="Jet type (charged or full)")
        args.add_argument("--recombinationscheme", metavar="RECOMBINATIONSCHEME", type=str, default="Escheme", help="Recombination scheme")
        args.add_argument("--yboost", metavar="YBOOST", type=float, default=0., help="Rapidity boost")
        args.add_argument("--ptmin", metavar="PTMIN", type=float, default=-1., help="Min. pt. (all constituents)")
        args.add_argument("--ptmincharged", metavar="PTMINCHARGED", type=float, default=-1., help="Min. pt. (charged constituents)")
        args.add_argument("--ptminneutral", metavar="PTMINNEUTRAL", type=float, default=-1., help="Min. pt. (neutral constituents)")
        args.add_argument("--emin", metavar="EMIN", type=float, default=-1., help="Min. E (all constituents)")
        args.add_argument("--emincharged", metavar="EMINCHARGED", type=float, default=-1., help="Min. E (charged constituents)")
        args.add_argument("--eminneutral", metavar="EMINNEUTRAL", type=float, default=-1., help="Min. E (neutral constituents)")

    def parse_args(self, args):
        if args.tune > -1:
            self.set_tune(args.tune)
        if args.pdfset > -1:
            self.set_pdf(args.pdfset)
        self.set_mpi(args.with_mpi)
        self.set_decay(False if not args.no_decay else True)
        self.set_jettype(args.jettype)
        self.set_recombinationscheme(args.recombinationscheme)
        if args.yboost != 0.:
            self.set_yboost(args.yboost)
        if args.ptmin > -1:
            self.set_ptecut(args.ptmin, False, True, False)
        if args.ptmincharged > -1:
            self.set_ptecut(args.ptmin, False, False, True)
        if args.ptminneutral > -1:
            self.set_ptecut(args.ptmin, False, False, False)
        if args.emin > -1:
            self.set_ptecut(args.ptmin, True, True, False)
        if args.emincharged > -1:
            self.set_ptecut(args.ptmin, True, False, True)
        if args.eminneutral > -1:
            self.set_ptecut(args.ptmin, True, False, False)

    def log(self):
        mpistring = "Not set"
        if self.__mpi.is_initialised():
            mpistring = "On" if self.__mpi.value else "Off"
        decaystring = "Not set"
        if self.__decay.is_initialised():
            decaystring = "On" if self.__decay.value else "Off"
        logging.info("Pythia simulation parameters:")
        logging.info("===============================================================")
        logging.info("  Tune:                  {}".format(self.__tune.value if self.__tune.is_initialised() else "Not set"))
        logging.info("  PDF set:               {}".format(self.__pdfset.value if self.__pdfset.is_initialised() else "Not set"))
        logging.info("  Jet type:              {}".format(self.__jettype.value if self.__jettype.is_initialised() else "Not set"))
        logging.info("  Recombination scheme:  {}".format(self.__recombinationScheme.value if self.__recombinationScheme.is_initialised() else "Not set"))
        logging.info("  MPI:                   {}".format(mpistring))
        logging.info("  Decays:                {}".format(decaystring))
        logging.info("  Min. pt:               {}".format(self.__ptcut.value if self.__ptcut.is_initialised() else "Not set"))
        logging.info("  Min. pt (charged):     {}".format(self.__ptcutcharged.value if self.__ptcutcharged.is_initialised() else "Not set"))
        logging.info("  Min. pt (neutral):     {}".format(self.__ptcutneutral.value if self.__ptcutneutral.is_initialised() else "Not set"))
        logging.info("  Min. E:                {}".format(self.__ecut.value if self.__ecut.is_initialised() else "Not set"))
        logging.info("  Min. E (charged):      {}".format(self.__ecutcharged.value if self.__ecutcharged.is_initialised() else "Not set"))
        logging.info("  Min. E (neutral):      {}".format(self.__ecutneutral.value if self.__ecutneutral.is_initialised() else "Not set"))
        logging.info("  y-boost:               {}".format(self.__yboost.value if self.__yboost.is_initialised() else "Not set"))
        