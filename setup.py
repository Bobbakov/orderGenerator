from setuptools import setup

setup(
    name = "ordergenerator",
    version = "0.1",
    description = "Agent-based modeling of markets",
    url = "http://github.com/bobbakov/orderGenerator",
    author = "main author",
    author_email = "main.author@email.com",
    license = "GPL3",
    packages = ["ordergenerator"],
    install_requires = ["seaborn", "matplotlib", "numpy", ],
    zip_safe = False
)