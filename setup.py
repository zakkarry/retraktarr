import os

from distutils.core import setup
from setuptools import find_packages

# User-friendly description from README.md
current_directory = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(current_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except Exception:
    long_description = ""

try:
    with open(os.path.join(current_directory, "VERSION"), encoding="utf-8") as f:
        version_no = f.read()
except Exception as e:
    print(e)
    version_no = "a"

setup(
    # Name of the package
    name="retraktarr",
    # Start with a small number and increase it with
    # every change you make https://semver.org
    # Chose a license from here: https: //
    # help.github.com / articles / licensing - a -
    # repository. For example: MIT
    license="MIT",
    version=version_no,
    # Short description of your library
    description=("a simple Arr -> Trakt.tv list sync script"),
    # Long description of your library
    install_requires="requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # Your name
    author="zakkarry",
    # Your email
    author_email="",
    # Either the link to your github or to your website
    url="https://github.com/zakkarry",
    # Link from which the project can be downloaded
    download_url="https://github.com/zakkarry/reTraktarr",
    packages=find_packages("."),
    package_dir={"": "."},
    include_package_data=True,
)
