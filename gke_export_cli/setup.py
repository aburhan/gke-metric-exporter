from setuptools import setup, find_packages

setup(
    name='gke-metrics-tool',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'pandas',
        'google-auth',
        'google-api-python-client',
 
    ],
    entry_points={
        'console_scripts': [
            'gke-metrics=cli:main',  # This will create the `gke-metrics` command for the CLI
        ],
    },
)
