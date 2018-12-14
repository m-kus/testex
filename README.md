# TestEx
[![Build Status](https://img.shields.io/travis-ci/m-kus/testex.svg?branch=master)](https://travis-ci.com/m-kus/testex)
[![Maintainability](https://img.shields.io/codeclimate/maintainability/m-kus/testex.svg?)](https://codeclimate.com/github/m-kus/testex/maintainability)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/f6869fca21474a82a50b04e474ba63e4?)](https://www.codacy.com/app/m-kus/testex)
[![Made With](https://img.shields.io/badge/made%20with-python-blue.svg?)](https://www.python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg?)](https://www.gnu.org/licenses/gpl-3.0)

TestEx is a universal and standalone service for testing crypto-exchange API interaction with your code.
It behaves almost exactly as a particular exchange itself.

![No more debugging in production!](https://memegenerator.net/img/instances/60032167/every-time-you-debug-in-production-god-kills-a-1000-kittens.jpg?)

## Supported exchanges

|Exchange|API version|Revised in TestEx|Documentation|
|--------|-----------|------------|-------------|
|Bittrex |v1.1       |10.12.18    |[docs](https://bittrex.github.io/api/v1-1)|
|Poloniex|v1.0       |10.12.18    |[docs](https://poloniex.com/support/api/)|

## Requirements

* git
* docker>=17 [how to install on ubuntu](https://thishosting.rocks/install-docker-on-ubuntu/)

## Installation

```
# Clone this repository
$ git clone https://github.com/m-kus/testex.git

# Go into the folder
$ cd testex

# Build and run project in daemon mode
$ docker-compose up -d --build

# Shutdown
$ docker-compose down
```

## Usage

### Modify api urls

Set base url in your custom wrapper or patch third party libraries.

```
https://bittrex.com/api/v1.1/public/getmarkets  # before
http://127.0.0.1:8008/bittrex.com/api/v1.1/public/getmarkets  # after

https://poloniex.com/public?command=returnTicker  # before
http://127.0.0.1:8008/poloniex.com/public?command=returnTicker  # after
```

### Make a deposit

Open [http://127.0.0.1:8008/deposit](http://127.0.0.1:8008/deposit) in your browser and make a deposit.

You can also do this from code, for example:
```python
import requests
from decimal import Decimal

requests.post('http://127.0.0.1:8008/deposit', data=dict(
    api_key='API_KEY',
    currency='BTC',
    amount=Decimal('100')
))
```

### Watch logs

```
$ docker logs testex

# In real-time
$ docker logs testex -ft 
```

### View data

Connect directly to the database via ```mongodb://127.0.0.1:27018/testex```

## Planned features

* More complicated execution (market/limit orders, ioc, fok, post)
* Connection reset simulation
* Rate limit emulation
* Support top 5 exchanges
* Autonomous market data generator
* Websocket API
* Deposit/withdrawals in testnet
* TestEx as a service
