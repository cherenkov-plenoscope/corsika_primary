#!/usr/bin/env python
# Copyright 2017-2021 Sebastian A. Mueller
import os
import argparse
import corsika_primary as cpw


def main():
    parser = argparse.ArgumentParser(
        prog="corsika_primary_install.py",
        description=(
            "Install the CORSIKA-primary-modification."
            + "Caches the CORSIKA-download. "
            + "Username and password are only needed once for download."
        ),
    )
    parser.add_argument(
        "--install_path",
        metavar="PATH",
        type=str,
        help="The directory to install the CORSIKA-primary-mod to.",
        nargs=1,
    )
    parser.add_argument(
        "--resource_path",
        metavar="PATH",
        type=str,
        help="The directory to the CORSIKA-primary-mod's resources.",
        nargs=1,
    )
    parser.add_argument(
        "--username",
        metavar="STRING",
        type=str,
        help="KIT CORSIKA's username for downloads.",
        default=None,
        nargs=1,
    )
    parser.add_argument(
        "--password",
        metavar="STRING",
        type=str,
        help="KIT CORSIKA's password for downloads.",
        default=None,
        nargs=1,
    )
    args = parser.parse_args()

    install_path = os.path.abspath(args.install_path[0])
    resource_path = os.path.abspath(args.resource_path[0])
    os.makedirs(install_path, exist_ok=True)
    corsika_tar_path = os.path.join(
        install_path, cpw.install.CORSIKA_TAR_FILENAME
    )

    if not os.path.exists(corsika_tar_path):
        if args.username is None or args.password is None:
            print("To download from KIT we need both username and password.")
            parser.print_help()
            return 1

        print("Downloading from KIT...")
        cpw.install.download_corsika_tar(
            output_dir=install_path,
            username=args.username[0],
            password=args.password[0],
            web_path=cpw.install.WEB_PATH,
            corsika_tar_filename=cpw.install.CORSIKA_TAR_FILENAME,
        )

    assert (
        cpw.install.CORSIKA_75600_TAR_GZ_HASH_HEXDIGEST
        == cpw.install.md5sum(corsika_tar_path)
    )

    vanilla_path = os.path.join(install_path, "vanilla")
    if not os.path.exists(vanilla_path):
        cpw.install.install_corsika(
            corsika_tar_path=corsika_tar_path,
            install_path=vanilla_path,
            resource_path=resource_path,
        )

    modified_path = os.path.join(install_path, "modified")
    if not os.path.exists(modified_path):
        cpw.install.install_corsika(
            corsika_tar_path=corsika_tar_path,
            install_path=modified_path,
            resource_path=resource_path,
            modify=True,
            vanilla_path=vanilla_path,
        )
    return 0


if __name__ == "__main__":
    main()
