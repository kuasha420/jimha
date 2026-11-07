from setuptools import setup, find_packages

setup(
    name="jimha",
    version="1.0.1",
    description="JimHa's Magical Key Smash Game - Fullscreen kid-friendly interactive wonderland",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md", encoding="utf-8") else "",
    long_description_content_type="text/markdown",
    author="Arafat Zahan",
    author_email="kuasha420@gmail.com",
    url="https://github.com/kuasha420/jimha",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
    ],
    entry_points={
        "gui_scripts": [
            "jimha = jimha.cli:run",
        ],
        "console_scripts": [
            "jimha-cli = jimha.cli:run",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Games/Entertainment",
    ],
)
