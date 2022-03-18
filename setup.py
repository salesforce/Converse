import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="converse-test-command",
    version="0.2.9",
    author="Salesforce Research",
    author_email="converse.ai@salesforce.com",
    description="A framework that facilitates creating task-oriented chatbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MetaMind/eloq_dial",
    project_urls={
        "Bug Tracker": "https://github.com/MetaMind/eloq_dial/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "black==20.8b1",
        "grpcio==1.27.2",
        "flake8==3.8.4",
        "flask==1.1.1",
        "Flask-Cors==3.0.9",
        "fuzzysearch==0.7.0",
        "jsonpickle==1.4.2",
        "nltk==3.6.6",
        "num2words==0.5.10",
        "pony==0.7.14",
        "protobuf==3.15.0",
        "python-Levenshtein==0.12.2",
        "thefuzz==0.19.0",
        "pyyaml==5.4",
        "redis==3.5.3",
        "requests==2.23.0",
        "scikit-learn==0.22.2.post1",
        "wrapt_timeout_decorator==1.3.1",
    ],
    entry_points={
        "console_scripts": [
            "converse-shell=Converse.demo.shell:main",
            "converse-build=Converse.demo.shell:build",
            "converse-demo=Converse.demo.shell:demo",
        ],
    },
    packages=setuptools.find_packages(exclude=["test_files"]),
    python_requires=">=3.7",
)
