#! /usr/bin/env python3
import logging
import os

def create_containerwrapper(runcommand: str, workdir: str, cluster: str, osversion: str):
    stagedir = os.path.join(workdir, "stage")
    if not os.path.exists(stagedir):
        os.makedirs(stagedir, 0o755)
    containerwrapper = os.path.join(stagedir, "containerwrapper.sh")
    logging.info("Creating container wrapper: %s", containerwrapper)
    with open(containerwrapper, "w") as containerwriter:
        containerwriter.write("#! /bin/bash\n")
        containerwriter.write("echo \"Running on host: $HOSTNAME\"\n")
        if cluster == "CADES":
            containerrepo = "/nfs/data/alice-dev/mfasel_alice"
            containertype = ""
            if osversion == "CentOS7":
                containertype = "mfasel_cc7_alice.simg"
            elif osversion == "CentOS8":
                containertype = "mfasel_cc8_alice.simg"
            image = os.path.join(containerrepo, containertype)
            binds = "-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
            containercommand = f"singularity exec {binds} {image} {runcommand}"
            containerwriter.write("module load PE-gnu\n")
            containerwriter.write("module load singularity\n")
            containerwriter.write("export SINGULARITYENV_SLOT=$SLURM_ARRAY_TASK_ID\n")
            containerwriter.write(f"{containercommand}\n")
        elif cluster == "CORI":
            containercommand = f"shifter --module=cvmfs -e SLOT=SLOT=$SLURM_ARRAY_TASK_ID {runcommand}"
            containerwriter.write(f"{containercommand}\n")
        containerwriter.close()
    return containerwrapper