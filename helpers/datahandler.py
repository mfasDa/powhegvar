#! /usr/bin/env python3
import os

def find_pwgevents(inputdir: str, eventfile: str = "pwgevents.lhe"):
	result = []
	for root, dirs, files in os.walk(inputdir):
		for fl in files:
			if eventfile in fl:
				result.append(os.path.join(os.path.abspath(root), fl))
	return sorted(result)