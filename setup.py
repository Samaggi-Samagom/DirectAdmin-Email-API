from setuptools import setup

with open("README", 'r') as f:
    long_description = f.read()

setup(
   name='DirectAdmin_API',
   version='1.0',
   description='Python API for Managing MXRoute Email Accounts through DirectAdmin API',
   long_description=long_description,
   author='Pakkapol Lailert',
   author_email='booklailert@gmail.com',
   packages=['DirectAdmin_API'],
   install_requires=['requests'],
)