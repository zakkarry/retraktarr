import os

from setuptools import setup, find_packages

"""
setup file for package publishing
"""
# User-friendly description from README.md
current_directory = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(current_directory, "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = f.read()
except OSError as e:
    LONG_DESCRIPTION = ""

try:
    with open(
        os.path.join(current_directory, f"retraktarr{os.path.sep}VERSION"),
        encoding="utf-8",
    ) as f:
        VERSION_NO = f.read()
except OSError as e:
    VERSION_NO = ""


with open("requirements.txt") as reqs_file:
    requirements = reqs_file.read().splitlines()

setup(
    # Name of the package
    name="retraktarr",
    # Start with a small number and increase it with
    # every change you make https://semver.org
    # Chose a license from here: https: //
    # help.github.com / articles / licensing - a -
    # repository. For example: MIT
    license="MIT",
    version=VERSION_NO,
    # Short description of your library
    description=("a simple Arr -> Trakt.tv list sync script"),
    entry_points={"console_scripts": ["retraktarr = retraktarr:main"]},
    # Long description of your library
    install_requires=requirements,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # Your name
    author="zakkarry",
    # Your email
    author_email="zak@ary.dev",
    # Either the link to your github or to your website
    url="https://github.com/zakkarry",
    # Link from which the project can be downloaded
    download_url="https://github.com/zakkarry/retraktarr",
    packages=find_packages(exclude=[".github"]),
    package_data={"retraktarr": ["VERSION"]},
)
