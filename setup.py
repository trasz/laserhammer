import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="laserhammer",
    version="2.4",
    author="Edward Tomasz Napierała",
    author_email="trasz@FreeBSD.org",
    description="DocBook to mdoc(7) converter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trasz/laserhammer",
    packages=setuptools.find_packages(),
    scripts = ['scripts/laserhammer'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Utilities",
    ],
)
