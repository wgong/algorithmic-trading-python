# Algorithmic Trading in Python


[Algorithmic Trading Using Python - Full Course](https://www.youtube.com/watch?v=xfzGZB4HhEE) 
developed by [Nick McCullum](https://nickmccullum.com/)

This repository

## Course Outline

* Section 1: Algorithmic Trading Fundamentals
  * What is Algorithmic Trading?
  * The Differences Between Real-World Algorithmic Trading and This Course
* Section 2: Course Configuration & API Basics
  * How to Install Python
  * Cloning The Repository & Installing Our Dependencies
  * Jupyter Notebook Basics
  * The Basics of API Requests
* Section 3: Building An Equal-Weight S&P 500 Index Fund
  * Theory & Concepts
  * Importing our Constituents
  * Pulling Data For Our Constituents
  * Calculating Weights
  * Generating Our Output File
  * Additional Project Ideas
* Section 4: Building A Quantitative Momentum Investing Strategy
  * Theory & Concepts
  * Pulling Data For Our Constituents
  * Calculating Weights
  * Generating Our Output File
  * Additional Project Ideas
* Section 5: Building A Quantitative Value Investing Strategy
  * Theory & Concepts
  * Importing our Constituents
  * Pulling Data For Our Constituents
  * Calculating Weights
  * Generating Our Output File
  * Additional Project Ideas


## IEX Cloud

https://iexcloud.io/

25% off annual plan  (CLOUDHOLIDAY2020)

## Issues

### pip install XlsxWriter not working on Ubuntu

with pip install, `import xlsxwriter` failed, solution is to install from source

```
$ git clone https://github.com/jmcnamara/XlsxWriter.git
$ cd XlsxWriter
$ python setup.py install
```

Not really, it has something to do with vscode Integrated terminal.
