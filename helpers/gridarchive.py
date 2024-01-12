#! /usr/bin/env python3

import logging
import os
import shutil
from zipfile import ZipFile

class gridarchive(object):

    def __init__(self):
        self.__gridfiles = []

    def add_file(self, filename: str):
        self.__gridfiles.append(filename)

    def add_files(self, files: list):
        self.__gridfiles += files

    def list(self):
        def proclog(gtype: str, files: list):
            logging.info("%s:", gtype)
            logging.info("================================")
            for f in files:
                logging.info(f)
        proclog("Grids", sorted(self.__get_grids()))
        proclog("Ubounds", sorted(self.__get_ubounds()))
        proclog("Xgridinfos", sorted(self.__get_xginfos()))

    def is_parallel_mode(self) -> bool:
        return self.number_grids() > 1

    def is_single_mode(self) -> bool:
        return not self.is_parallel_mode()

    def check(self) -> bool:
        ngrids = self.number_grids()
        nubounds = self.number_ubounds()
        nxginfo = self.number_xginfos()
        if ngrids == 0 or nubounds == 0 or nxginfo == 0:
            return False
        return ngrids == nubounds and ngrids == nxginfo and nubounds == nxginfo
    
    def build(self, filename: str, force_overwrite: bool = False) -> bool:
        if os.path.exists(filename):
            if force_overwrite:
                logging.warning("Overwriting existing grid archive %s", filename)
                os.remove(filename)
            else:
                logging.warning("Grid archive %s already existing, not overwriting", filename)
                return False
        compressor = ZipFile(filename, "w")
        for fl in sorted(self.__gridfiles):
            compressor.write(fl)
        compressor.close()
        return True

    def extract(self, filename: str) -> bool:
        if not os.path.exists(filename):
            logging.error("Grid archive %s not existing, cannot extract", filename)
            return False
        extractor = ZipFile(filename, "r")
        for f in extractor.filelist:
            if not f in self.__gridfiles:
                self.__gridfiles.append(f.filename)
        extractor.extractall()
        extractor.close()
        return True

    def stage(self, griddir: str, workdir: str):
        for x in self.__gridfiles:
            inputfile = os.path.join(griddir, x)
            outputfile = os.path.join(workdir, x)
            if os.path.exists(inputfile):
                shutil.copyfile(inputfile, outputfile)

    def clean_gridfiles(self, workdir: str):
        for f in self.__gridfiles:
            fullgridfilename = os.path.join(workdir, f)
            if os.path.exists(fullgridfilename):
                os.remove(fullgridfilename) 

    def number_allgrids(self) -> int:
        return len(self.__gridfiles)

    def number_grids(self) -> int:
        return len(self.__get_grids())
    
    def number_ubounds(self) -> int:
        return len(self.__get_ubounds())

    def number_xginfos(self) -> int:
        return len(self.__get_xginfos())
    
    def __get_grids(self) -> list:
        return [x for x in self.__gridfiles if "pwggrid" in x and not "info" in x]

    def __get_ubounds(self) -> list:
        return [x for x in self.__gridfiles if "pwgubound" in x]

    def __get_xginfos(self) -> list:
        return [x for x in self.__gridfiles if "pwggridinfo-btl-xg" in x or "pwgxgrid" in x]

def find_gridfiles_in_directory(griddir) -> list:
    def find_largest_xg_iteration(xgfiles: list) -> int:
        iters = []
        for fl in xgfiles:
            toks = fl.split("-")
            for tok in toks:
                if "xg" in tok:
                    iter = int(tok.replace("xg", ""))
                    if not iter in iters:
                        iters.append(iter)
        return max(iters)
    gridfiles = []
    xgfiles = []
    datfiles = [x for x in os.listdir(griddir) if x.endswith(".dat")]
    for f in datfiles:
        if "pwggridinfo-btl-xg" in f:
            xgfiles.append(f)
        else:
            if "pwggrid" in f or "pwgubound" in f or "pwgxgrid" in f:
                gridfiles.append(f)
    if len(xgfiles):
        maxiter = find_largest_xg_iteration(xgfiles)
        selxgfiles = [x for x in xgfiles if f"xg{maxiter}" in x]
        gridfiles += selxgfiles
    return gridfiles

def stage_gridfiles(griddir: str, workdir: str):
    for f in find_gridfiles_in_directory(griddir):
        shutil.copyfile(os.path.join(griddir, f), os.path.join(workdir,f))

def init_archive(griddir: str) -> gridarchive:
    archive = gridarchive()
    archive.add_files(find_gridfiles_in_directory(griddir))
    return archive

def build_archive(griddir: str, force_overwrite: bool = False, clean: bool = False):
    archive = init_archive(griddir)
    if archive.check():
        logging.info("Grid files consistent, building archive ...")
        archive.list()
        currentdir = os.getcwd()
        os.chdir(griddir)
        archive.build("grids.zip", force_overwrite)
        if clean:
            archive.clean_gridfiles(griddir)
        os.chdir(currentdir)
        logging.info("Grid archive can be found under %s", os.path.join(griddir, "grids.zip"))
    else:
        logging.error("Grids inconsistent, cannot create archive")