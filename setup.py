from setuptools import setup
setup(
    install_requires=[
        "meerk40t>=0.7.0-post11",
        "Flask"
    ],
    package_data = {"restk40t" : ["templates/index.html"]}
)
