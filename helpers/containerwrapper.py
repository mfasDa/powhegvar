#! /usr/bin/env python3
import logging
import os

def create_containerwrapper(workdir: str, cluster: str, osversion: str):
    stagedir = os.path.join(workdir, "stage")
    if not os.path.exists(stagedir):
        os.makedirs(stagedir, 0o755)
    containerwrapper = os.path.join(stagedir, f"containerwrapper_{cluster}_{osversion}.sh")
    if os.path.exists(containerwrapper):
        logging.info("Container wrapper already existing - not creating again ...")
        return containerwrapper
    logging.info("Creating container wrapper: %s", containerwrapper)
    with open(containerwrapper, "w") as containerwriter:
        containerwriter.write("#! /bin/bash\n")
        containerwriter.write("echo \"Running on host: $HOSTNAME\"\n")
        containercommand = ""
        if cluster == "CADES":
            containerrepo = "/nfs/data/alice-dev/mfasel_alice"
            containertype = ""
            if osversion == "CentOS7":
                containertype = "mfasel_cc7_alice.simg"
            elif osversion == "CentOS8":
                containertype = "mfasel_cc8_alice.simg"
            image = os.path.join(containerrepo, containertype)
            binds = "-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
            containercommand = f"singularity exec {binds} {image}"
            containerwriter.write("module load PE-gnu\n")
            containerwriter.write("module load singularity\n")
            containerwriter.write("export SINGULARITYENV_SLOT=$SLURM_ARRAY_TASK_ID\n")
        elif cluster == "PERLMUTTER":
            containercommand = f"shifter --clearenv --module=cvmfs -e SLOT=$SLURM_ARRAY_TASK_ID -e HOME=$HOME"
        elif cluster == "B587":
            containerrepo = "/cvmfs/alice.cern.ch/containers/fs/singularity"
            containertype = "rel8-alice-20220503"
            singularity_app="/cvmfs/alice.cern.ch/containers/bin/apptainer/current/bin/apptainer"
            image = os.path.join(containerrepo, containertype)
            binds = "-B /cvmfs:/cvmfs-B /software:/software -B /alf:/alf"
            containercommand = f"{singularity_app} exec -C {binds} {image}"
            containerwriter.write("export SINGULARITYENV_SLOT=$SLURM_ARRAY_TASK_ID\n")
        containerwriter.write(f"RUNCMD=\"{containercommand}\"\n")
        containerwriter.write("for arg in \"$@\"; do\n")
        concatstring = "    RUNCMD=$(printf \"%s %s\" \"$RUNCMD\" \"$arg\")\n" 
        containerwriter.write(concatstring)
        containerwriter.write("done\n")
        containerwriter.write("echo \"Running: $RUNCMD\"\n")
        containerwriter.write("eval $RUNCMD\n")
        containerwriter.close()
    return containerwrapper