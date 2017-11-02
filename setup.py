from distutils.core import setup

version = '1.0'

setup(
    name='IntegraPy',
    version=version,
    description=u"Satel's Integra secrity hub interface",
    author='Marcin Korzonek & Michał Węgrzynek & al.',
    packages=[
        'IntegraPy'
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'bitarray'
    ]
)
