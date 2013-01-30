from setuptools import setup, find_packages

from subforms import VERSION


setup(
    name='django-subforms',
    version='.'.join(map(str, VERSION)),
    description='Hierarchical subform and form field to model mapping system',
    long_description=open('README.rst').read(),
    author='Gavin McQuillan, Chris Dickinson',
    author_email='gavin@urbanairship.com, chris.dickinson@urbanairship.com',
    url='http://github.com/urbanairship/django-subforms',
    license=open('LICENSE').read(),
    packages=find_packages(),
    include_package_data=True,
    package_data = { '': ['README.rst'] },
    zip_save=False,
    install_requires=[
        'django',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

