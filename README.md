# MyUber: Distributed Ride-Sharing Platform

## Overview

MyUber is a distributed ride-sharing platform implemented using gRPC with SSL/TLS encryption. It provides a secure and efficient way to manage ride requests, driver assignments, and ride statuses.

## Features

- Secure communication using SSL/TLS
- Driver management system
- Ride request and assignment
- Real-time ride status updates
- Automatic ride reassignment on timeout or rejection
- Comprehensive logging system
- Authentication and error handling interceptors

## Prerequisites

- Python 3.7+
- gRPC
- OpenSSL (for generating SSL/TLS certificates)

## Installation

1. Install the required packages:

```
  pip install grpcio grpcio-tools protobuf
```


2. Generate SSL certificates:

```bash
  # Generate CA key and certificate
  openssl genrsa -out ca.key 2048
  openssl req -new -x509 -days 365 -key ca.key -out ca.crt

  # Generate server key and CSR
  openssl genrsa -out server.key 2048
  openssl req -new -key server.key -out server.csr

  # Generate server certificate
  openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt

  # Generate client key and CSR
  openssl genrsa -out client.key 2048
  openssl req -new -key client.key -out client.csr

  # Generate client certificate
  openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 02 -out client.crt
```

3. Generate gRPC code:

```
  ython -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. myuber.proto
```

## Usage

1. Start the server:

```
  python myuber_server.py
```

2. Run the driver instances:

```
  python myuber_driver.py
```

3. Run the client instances:

```
  python myuber_client.py
```

## Code Structure

- `myuber.proto`: Protocol buffer definition file
- `myuber_server.py`: Main server implementation
- `myuber_client.py`: Client implementation
- `myuber_interceptors.py`: Authentication and logging interceptors
- `myuber_logger.py`: Logging configuration

## Features


- Secure communication using SSL/TLS
- Multiple concurrent drivers and clients
- Ride request, assignment, acceptance, rejection, and completion
- Automatic ride rejection after 10-second timeout
- Logging of all major events
