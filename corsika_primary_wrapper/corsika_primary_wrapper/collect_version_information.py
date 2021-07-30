import os
import io


def strip_coconut_config(coconut_config_header):
    """
    Strip empty lines, and comment-lines from config header.
    Only keep the '#define' directives.

    Parameters
    ----------
    coconut_config_header : str
            The text of the CORSIKA-coconut config header.
    """
    out = io.StringIO()
    for line in coconut_config_header.split('\n'):
        if len(line) > 0:
            if line[0] == '#':
                out.write(str.strip(line) + "\n")
    out.seek(0)
    return out.read()


def get_coconut_config_header(corsika_path, strip=False):
    """
    Gather the result of CORSIKA's coconut build tool. The coconut config.h
    stores all the build-options chosen by the user and can be used to
    build CORSIKA without manually enerting the build-options into coconut
    again.

    Parameters
    ----------
    corsika_path : str
            Path to corsika's executable in its 'run' directory.
    """
    run_dir = os.path.dirname(corsika_path)
    build_dir = os.path.dirname(run_dir)
    config_header_path = os.path.join(build_dir, "include", "config.h")

    with open(config_header_path, "rt") as f:
        config_header = f.read()

    if strip:
        return strip_coconut_config(config_header)
    else:
        return config_header
