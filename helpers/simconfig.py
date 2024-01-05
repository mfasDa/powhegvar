#! /usr/bin/env python3

class SimConfig:

    def __init__(self):
        self.__workdir = ""
        self.__powhegversion = ""
        self.__powheginput = ""
        self.__nevents = 0
        self.__scalereweight = False
        self.__minpdf = -1 
        self.__maxpdf = -1
        self.__minID = 0
        self.__minslot = -1
        self.__gridrepository = ""
        self.__process = ""
    
    def set_workdir(self, workdir: str):
        self.__workdir = workdir

    def set_powhegversion(self, version):
        self.__powhegversion = version

    def set_powheginput(self, powheginput: str):
        self.__powheginput = powheginput

    def set_nevents(self, nevents: int):
        self.__nevents = nevents

    def set_scalereweight(self, doSet: bool):
        self.__scalereweight = doSet

    def set_pdf_range(self, minpdf, maxpdf):
        self.__minpdf = minpdf
        self.__maxpdf = maxpdf

    def set_min_pdf(self, minpdf: int):
        self.__minpdf = minpdf

    def set_max_pdf(self, maxpdf: int):
        self.__maxpdf = maxpdf

    def set_minID(self, minID: int):
        self.__minID = minID

    def set_minslot(self, minslot: int):
        self.__minslot = minslot

    def set_gridrepository(self, gridrepository: str):
        self.__gridrepository = gridrepository

    def set_process(self, procname: str):
        self.__process = procname

    def get_workdir(self) -> str:
        return self.__workdir

    def get_powhegversion(self) -> str:
        return self.__powhegversion

    def get_powheginput(self) -> str:
        return self.__powheginput

    def get_nevents(self) -> int:
        return self.__nevents

    def get_pdf_range(self) -> tuple:
        return (self.__minpdf, self.__maxpdf)

    def get_min_pdf(self) -> int:
        return self.__minpdf
    
    def get_max_pdf(self) -> int:
        return self.__maxpdf

    def get_minID(self) -> int:
        return self.__minID

    def get_minslot(self) -> int:
        return self.__minslot

    def get_gridrepository(self) -> str:
        return self.__gridrepository

    def get_process(self) -> str:
        return self.__process
    
    def is_scalereweight(self) -> bool:
        return self.__scalereweight

    def is_pdfreweight(self) -> bool:
        return self.__minpdf > 0 and self.__maxpdf > 0

    workdir = property(fget=get_workdir, fset=set_workdir)
    powhegversion = property(fget=get_powhegversion, fset=set_powhegversion)
    powheginput = property(fget=get_powheginput, fset=set_powheginput)
    nevents = property(fget=get_nevents, fset=set_nevents)
    scalereweight = property(fget=is_scalereweight, fset=set_scalereweight)
    minpdf = property(fget=get_min_pdf, fset=set_min_pdf)
    maxpdf = property(fget=get_max_pdf, fset=set_max_pdf)
    minID = property(fget=get_minID, fset=set_minID)
    minslot = property(fget=get_minslot, fset=set_minslot)
    gridrepository = property(fget=get_gridrepository, fset=set_gridrepository)
    process = property(fget=get_process, fset=set_process)

    def print(self):
        print(f"Workdir:             {self.__workdir}")
        print(f"POWHEG version:      {self.__powhegversion}")
        print(f"POWHEG input:        {self.__powheginput}")
        print(f"Number of events:    {self.__nevents}")
        print(f"Process:             {self.__process}")
        print(f"Grid repository:     {self.__gridrepository}")
        print(f"Min. ID:             {self.__minID}")
        print(f"Min. Slot:           {self.__minslot}")
        print(f"Min. PDF:            {self.__minpdf}")
        print(f"Max. PDF:            {self.__maxpdf}")
        print("Scale reweight:      %s" %("Yes" if self.__scalereweight else "No"))

def get_batch_executable(config: SimConfig) -> str:
    if config.is_scalereweight():
        return "run_powheg_singularity_pdf.sh"
    elif config.is_pdfreweight():
        return "run_powheg_singularity_scale.sh"
    else:
        return "run_powheg_singularity.sh"
