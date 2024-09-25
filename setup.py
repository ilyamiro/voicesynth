from setuptools import setup, find_packages

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")


setup(
    name="voicesynth",
    version="0.2.1",
    author="ilyamiro",
    author_email="ilyamiro.work@gmail.com",
    description="Package for realistic voice synthesis",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha'
    ],
    install_requires=[
        "torch",
        "numpy",
        "playsound"
    ],

)
