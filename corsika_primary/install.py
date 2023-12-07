import os
import tarfile
import shutil
import subprocess
import glob
import hashlib


CORSIKA_75600_TAR_GZ_HASH_HEXDIGEST = "9ef453eebc4bf5b8b04209b1acdebda2"

WEB_PATH = "https://web.ikp.kit.edu/corsika/download/old/v750/"
CORSIKA_NAME = "corsika-75600"
CORSIKA_TAR_FILENAME = CORSIKA_NAME + ".tar.gz"


def md5sum(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def diff(vanilla_path, modified_path, out_path):
    with open(out_path, "w") as stdout:
        subprocess.call(["diff", vanilla_path, modified_path], stdout=stdout)


def patch(vanilla_path, diff_path, out_path):
    subprocess.call(["patch", vanilla_path, diff_path, "-o", out_path])


def call_and_save_std(target, stdout_path, stderr_path, stdin=None):
    with open(stdout_path, "w") as stdout, open(stderr_path, "w") as stderr:
        subprocess.call(target, stdout=stdout, stderr=stderr, stdin=stdin)


def download_corsika_tar(
    output_dir,
    username,
    password,
    web_path,
    corsika_tar_filename,
):
    # download CORSIKA from KIT
    # wget uses $http_proxy environment-variables in case of proxy
    call_and_save_std(
        target=[
            "wget",
            "--no-check-certificate",
            "--directory-prefix",
            output_dir,
            "--user",
            username,
            "--password",
            password,
            web_path + corsika_tar_filename,
        ],
        stdout_path=os.path.join(
            output_dir, corsika_tar_filename + ".wget.stdout"
        ),
        stderr_path=os.path.join(
            output_dir, corsika_tar_filename + ".wget.stderr"
        ),
    )


def install_corsika(
    corsika_tar_path,
    install_path,
    resource_path,
    modify=False,
    vanilla_path=None,
):
    install_path = os.path.abspath(install_path)
    resource_path = os.path.abspath(resource_path)
    os.makedirs(install_path, exist_ok=True)

    # untar, unzip the CORSIKA download
    tar = tarfile.open(corsika_tar_path)
    tar.extractall(path=install_path)
    tar.close()

    # Go into CORSIKA dir
    corsika_basename = os.path.basename(
        os.path.splitext(os.path.splitext(corsika_tar_path)[0])[0]
    )
    corsika_path = os.path.join(install_path, corsika_basename)
    os.chdir(corsika_path)

    # Provide the coconut config.h
    corsika_config_path = os.path.join(resource_path, "config.h")
    shutil.copyfile(corsika_config_path, os.path.join("include", "config.h"))

    # coconut configure
    call_and_save_std(
        target=["./coconut"],
        stdout_path=os.path.join(install_path, "coconut_configure.stdout"),
        stderr_path=os.path.join(install_path, "coconut_configure.stderr"),
        stdin=open("/dev/null", "r"),
    )

    if modify:
        # apply modification to CORSIKA itslef.
        patch(
            vanilla_path=os.path.join(
                vanilla_path,
                CORSIKA_NAME,
                "src",
                "corsikacompilefile.f",
            ),
            diff_path=os.path.join(resource_path, "corsikacompilefile.f.diff"),
            out_path=os.path.join(
                "src",
                "corsikacompilefile.f",
            ),
        )

        # apply modifications to bernlohrs iact package.
        shutil.copy(
            os.path.join(resource_path, "mli_corsika_EventTape_headeronly.h"),
            os.path.join("bernlohr", "mli_corsika_EventTape_headeronly.h"),
        )
        shutil.copy(
            os.path.join(resource_path, "iact.c"),
            os.path.join("bernlohr", "iact.c"),
        )

    # coconut build
    call_and_save_std(
        target=["./coconut", "-i"],
        stdout_path=os.path.join(install_path, "coconut_make.stdout"),
        stderr_path=os.path.join(install_path, "coconut_make.stderr"),
    )

    # Copy default ATMPROFS to the CORSIKA run directory
    for atmprof in glob.glob(os.path.join("bernlohr", "atmprof*")):
        shutil.copy(atmprof, "run")

    # Copy additional ATMPROFS from sim-tel-array to the CORSIKA run directory
    add_atmprofs_path = os.path.join(resource_path, "atmprofs", "atmprof*")
    for atmprof in glob.glob(add_atmprofs_path):
        shutil.copy(atmprof, "run")

    assert os.path.isfile(os.path.join("run", "corsika75600Linux_QGSII_urqmd"))


def typical_corsika_primary_mod_path(build_dir="build"):
    return os.path.join(
        build_dir,
        "corsika",
        "modified",
        "corsika-75600",
        "run",
        "corsika75600Linux_QGSII_urqmd",
    )
