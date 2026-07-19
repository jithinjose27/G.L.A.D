from setuptools import find_packages, setup
from glob import glob

package_name = "glad_tour"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="root",
    maintainer_email="jithin27j@gmail.com",
    description="G.L.A.D. Autonomous Tour Guide Package",
    license="Apache 2.0",
    extras_require={"test": ["pytest"]},
    entry_points={
        "console_scripts": [
            "glad_tour=glad_tour.glad_tour:main",
        ],
    },
)
