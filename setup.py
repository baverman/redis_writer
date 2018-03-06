from setuptools import setup, find_packages

setup(
    name='redis_writer',
    version='0.3',
    url='https://github.com/baverman/redis_writer/',
    license='MIT',
    author='Anton Bobrov',
    author_email='baverman@gmail.com',
    description='Fast serializer to pipeline data into redis',
    long_description=open('README.rst').read(),
    py_modules=['redis_writer'],
    install_requires=['hiredis >= 0.2'],
    include_package_data=False,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Distributed Computing',
    ]
)
