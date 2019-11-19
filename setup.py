from setuptools import setup, find_packages

version = "1.0.0"

setup(
    name="senaite.autopublish",
    version=version,
    description="Automatic publication of results for SENAITE",
    long_description=open("README.rst").read() + "\n" +
    open("CHANGES.rst").read() + "\n",
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords=['senaite', 'lims', 'opensource'],
    author="Naralabs SL",
    author_email="info@naralabs.com",
    url="https://github.com/senaite/senaite.autopublish",
    license="GPLv2",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    namespace_packages=["senaite"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "selenium",
        "setuptools",
        "senaite.lims>=1.3.0",
        "senaite.lims<2.0.0",
        "senaite.queue",
    ],
    extras_require={
        "test": [
            "Products.PloneTestCase",
            "Products.SecureMailHost",
            "plone.app.testing",
            "unittest2",
        ]
    },
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
