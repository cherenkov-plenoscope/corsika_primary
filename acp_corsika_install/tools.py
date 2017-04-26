import subprocess


def call_and_save_std(target, stdout_path, stderr_path, stdin=None):
    """
    Same as subprocess.call, but stores the stdout and stderr to text files.

    Parameters
    ----------
    target          The target to be called with subprocess.call().

    stdout_path     The path where the stdout of the target call is written to.

    stderr_path     The path where the stderr of the target call is written to.

    stdin           Optional stdin fot the target.
    """
    stdout = open(stdout_path, 'w')
    stderr = open(stderr_path, 'w')
    subprocess.call(
        target,
        stdout=stdout, 
        stderr=stderr,
        stdin=stdin)
    stdout.close()
    stderr.close()