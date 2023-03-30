import os
import tempfile

from tools import run

try:
    # to test locally with an artifactory instance that already has
    # extensions-stg and extensions-prod repos, define this dict of credentials
    # in credentials.py (the file is gitignored)

    # environment = {
    #     "CONAN_LOGIN_USERNAME_EXTENSIONS_PROD": "......",
    #     "CONAN_PASSWORD_EXTENSIONS_PROD": "......",
    #     "CONAN_LOGIN_USERNAME_EXTENSIONS_STG": "......",
    #     "CONAN_PASSWORD_EXTENSIONS_STG": "......",
    #     "ART_URL": "https://url/artifactory",
    # }

    from credentials import environment
except ImportError:
    environment = {}

import pytest


@pytest.fixture(autouse=True)
def conan_test():
    old_env = dict(os.environ)
    env_vars = {"CONAN_HOME": tempfile.mkdtemp(suffix='conans')}
    os.environ.update(env_vars)
    os.environ.update(environment)
    current = tempfile.mkdtemp(suffix="conans")
    cwd = os.getcwd()
    os.chdir(current)
    run("conan profile detect")
    run(f'conan remote add extensions-prod {os.getenv("ART_URL")}/api/conan/extensions-prod')
    run(f'conan remote add extensions-stg {os.getenv("ART_URL")}/api/conan/extensions-stg')

    try:
        yield
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(old_env)


def test_build_info_create():
    repo = os.path.join(os.path.dirname(__file__), "..")

    build_name = "mybuildinfo"
    build_number = "1"

    run(f"conan config install {repo}")
    run("conan new cmake_lib -d name=mypkg -d version=1.0 --force")

    run("conan create . --format json -tf='' -s build_type=Release > create_release.json")
    run("conan create . --format json -tf='' -s build_type=Debug > create_debug.json")

    run("conan remove mypkg* -c -r extensions-stg")
    run("conan remove mypkg* -c -r extensions-prod")

    run("conan upload mypkg/1.0 -c -r extensions-stg")

    run(f'conan art:build-info create create_release.json {build_name}_release {build_number} > {build_name}_release.json')
    run(f'conan art:build-info create create_debug.json {build_name}_debug {build_number} > {build_name}_debug.json')

    run(f'conan art:property build-info-add {build_name}_release.json {os.getenv("ART_URL")} extensions-stg --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    run(f'conan art:property build-info-add {build_name}_debug.json {os.getenv("ART_URL")} extensions-stg --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    run(f'conan art:build-info upload {build_name}_release.json {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    run(f'conan art:build-info upload {build_name}_debug.json {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    run(f'conan art:build-info get {build_name}_release {build_number} {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')
    run(f'conan art:build-info get {build_name}_debug {build_number} {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    #run(f'conan art:build-info promote {build_name} {build_number} {os.getenv("ART_URL")} extensions-stg extensions-prod --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    #run(f'conan art:build-info get {build_name} {build_number} {os.getenv("ART_URL")} --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}"')

    #run(f'conan art:build-info delete {build_name} {os.getenv("ART_URL")} --build-number=1 --user="{os.getenv("CONAN_LOGIN_USERNAME_EXTENSIONS_STG")}" --password="{os.getenv("CONAN_PASSWORD_EXTENSIONS_STG")}" --delete-all --delete-artifacts')
