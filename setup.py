from distutils.core import setup

version = '1.0'

setup(
    name='IntegraPy',
    version=version,
    description=u"Satel's Integra secrity hub interface",
    author='M. Korz & Michał Węgrzynek',
    packages=[
        'IntegraPy'
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'bitarray'
    ]
)
