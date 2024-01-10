#! /usr/bin/env python3

import os
from datetime import datetime

def get_semaphore_name(workdir: str) -> str:
    return os.path.join(workdir, "pwgsemaphore.txt")

class pwsemaphore(object):

    def __init__(self, workdir: str, active: bool = False):
        self.__workdir = workdir
        self.__active = active

    def create(self):
        semaphorename = get_semaphore_name(self.__workdir)
        with open(semaphorename, "w") as semwriter:
            currenttime = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            semwriter.write(f"created: {currenttime}\n")
            semwriter.close()
        self.__active = True

    def remove(self):
        semaphorename = get_semaphore_name(self.__workdir)
        if os.path.exists(semaphorename):
            os.remove(semaphorename)
        self.__active = False

    def is_active(self) -> bool:
        return self.__active

    def set_active(self, isActive: bool):
        self.__active = isActive

def has_semaphore(workdir: str) -> pwsemaphore:
    semaphoreame = get_semaphore_name(workdir)
    if os.path.exists(semaphoreame):
        return pwsemaphore(workdir, True)
    return None