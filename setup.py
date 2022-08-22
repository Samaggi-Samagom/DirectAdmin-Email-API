from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='DirectAdminInterface',
   version='1.1.2',
   description='Python API for Managing MXRoute Email Accounts through DirectAdmin API',
   long_description=long_description,
   author='Pakkapol Lailert',
   author_email='booklailert@gmail.com',
   packages=['DirectAdminInterface'],
   install_requires=['requests'],
)