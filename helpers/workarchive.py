#! /usr/bin/env python3

import logging
import os
from zipfile import ZipFile

class FileNotFoundException(Exception):

    def __init__(self, filename: str):
        self.__filename = filename

    def __str__(self):
        return f"File {self.__filename} not found"

    def get_filename(self) -> str:
        return self.__filename

class WorkArchive(object):

    def __init__(self, archivename: str):
        self.__archivename = archivename
        self.__files = []

    def add(self, filename: str):
        if not os.path.exists(filename):
            raise FileNotFoundException(filename)
        self.__files.append(filename)

    def update(self):
        writemode = None
        if os.path.exists(self.__archivename):
            writemode = "a"
        else:
            writemode = "w"
        writer = ZipFile(self.__archivename, writemode)
        for workfile in sorted(self.__files):
            writer.write(workfile)
        writer.printdir()
        writer.close()

    def clean(self):
        for workfile in self.__files:
            if os.path.exists(workfile):
                os.remove(workfile)

def build_archive(name: str, files: list, clean: bool):
    if len(files):
        archivehandler = WorkArchive(name)
        for workfile in files:
            logging.info("Adding %s to archive %s", workfile, name)
            archivehandler.add(workfile)
        archivehandler.update()
        if clean:
            archivehandler.clean()


def pack_workarchives(workdir: str, clean: bool = True):
    basedir = os.getcwd()
    os.chdir(workdir)
    allfiles = [x for x in os.listdir(os.getcwd())]

    build_archive("logs.zip", [x for x in allfiles if x.endswith(".log")], clean)
    build_archive("inputs.zip", [x for x in allfiles if x.endswith(".input") and not "powheg_base" in x], clean)

    os.chdir(basedir)