import subprocess
import argparse
import datetime

from universal_build import build_utils

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "--flavor",
    help="flavor (full, light, minimal) used for docker container",
    default="gpu",
)

REMOTE_IMAGE_PREFIX = "mltooling/"
FLAG_FLAVOR = "flavor"
COMPONENT_NAME = "gpu-flavor"

args = build_utils.get_sanitized_arguments(argument_parser=parser)

if not args[FLAG_FLAVOR]:
    args[FLAG_FLAVOR] = "gpu"

args[FLAG_FLAVOR] = str(args[FLAG_FLAVOR]).lower()

if args[FLAG_FLAVOR] == "all":
    args[FLAG_FLAVOR] = "gpu"
    build_utils.build(".", args)
    build_utils.exit_process(0)

# unknown flavor -> try to build from subdirectory
if args[FLAG_FLAVOR] not in ["gpu"]:
    # assume that flavor has its own directory with build.py
    build_utils.build(args[FLAG_FLAVOR] + "-flavor", args)
    build_utils.exit_process(0)

service_name = COMPONENT_NAME + "-" + args[FLAG_FLAVOR]

# docker build
git_rev = "unknown"
try:
    git_rev = (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode("ascii")
        .strip()
    )
except Exception:
    pass

build_date = datetime.datetime.utcnow().isoformat("T") + "Z"
try:
    build_date = (
        subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"])
        .decode("ascii")
        .strip()
    )
except Exception:
    pass

vcs_ref_build_arg = " --build-arg ARG_VCS_REF=" + str(git_rev)
build_date_build_arg = " --build-arg ARG_BUILD_DATE=" + str(build_date)
flavor_build_arg = " --build-arg ARG_WORKSPACE_FLAVOR=" + str(args[FLAG_FLAVOR])
version_build_arg = " --build-arg ARG_WORKSPACE_VERSION=" + str(
    args[build_utils.FLAG_VERSION]
)

if args[build_utils.FLAG_MAKE]:
    build_args = (
        version_build_arg
        + " "
        + flavor_build_arg
        + " "
        + vcs_ref_build_arg
        + " "
        + build_date_build_arg
    )

    completed_process = build_utils.build_docker_image(
        COMPONENT_NAME, version=args[build_utils.FLAG_VERSION], build_args=build_args
    )
    if completed_process.returncode > 0:
        build_utils.exit_process(1)

if args[build_utils.FLAG_RELEASE]:
    build_utils.release_docker_image(
        COMPONENT_NAME,
        args[build_utils.FLAG_VERSION],
        args[build_utils.FLAG_DOCKER_IMAGE_PREFIX],
    )
