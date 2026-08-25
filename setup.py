from setuptools import setup, find_packages

setup(
name="digital_watermark",
version="0.1.0",
packages=find_packages(),
install_requires=[
"flask==2.3.3",
"numpy==1.26.4",
"opencv-python==4.8.1.78",
"PyWavelets==1.9.0",
"scikit-image==0.22.0",
"Werkzeug==2.3.7",
],
)