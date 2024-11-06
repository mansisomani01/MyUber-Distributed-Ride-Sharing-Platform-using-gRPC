# MyUber System Implementation Report

## Overview

The MyUber system is a simulated ride-sharing service implemented using gRPC and Python. It demonstrates key functionalities of a ride-sharing platform, including ride requests, driver assignments, and secure communication.

## Key Functionalities and Their Implementation

### 1. Secure Communication (SSL/TLS)

- Implemented using gRPC's SSL/TLS features.
- SSL certificates (CA, server, and client) are generated and used for all communications.
- In `myuber_server.py`, `grpc.ssl_server_credentials()` is used to set up secure server credentials.
- In `myuber_client.py` and `myuber_driver.py`, `grpc.ssl_channel_credentials()` is used to establish secure connections to the server.

### 2. Concurrent Handling of Multiple Drivers and Clients

- The server uses `grpc.server(futures.ThreadPoolExecutor(max_workers=10))` to handle multiple concurrent connections.
- Each driver and client runs in its own process, allowing for true concurrency.

### 3. Ride Request and Assignment

- Implemented in `MyUberServicer.RequestRide()` method in `myuber_server.py`.
- When a ride is requested, it's added to a queue (`self.ride_queue`).
- A separate thread (`allocate_rides()`) continuously processes this queue and assigns rides to available drivers.

### 4. Driver Registration

- Implemented in `MyUberServicer.RegisterDriver()` method.
- Drivers are added to a pool of available drivers managed by `DriverManager` class.

### 5. Ride Acceptance/Rejection with Timeout

- When a ride is assigned, a 10-second timer is started (`start_ride_timer()` in `myuber_server.py`).
- In `myuber_driver.py`, the driver has 10 seconds to accept or reject the ride.
- If no response is received within 10 seconds, the ride is automatically rejected (`handle_ride_timeout()` in `myuber_server.py`).

### 6. Ride Completion

- Implemented in `MyUberServicer.CompleteRide()` method.
- Drivers manually signal ride completion in `myuber_driver.py`.

### 7. Status Updates

- Clients can check ride status using `MyUberServicer.GetRideStatus()` method.
- Drivers check for assigned rides using `MyUberServicer.CheckForRide()` method.

### 8. Automatic Ride Reassignment

- If a ride is rejected (manually or due to timeout), it's put back in the queue for reassignment.
- Implemented in `MyUberServicer.RejectRide()` and `handle_ride_timeout()` methods.

### 9. Logging

- Centralized logging system implemented in `myuber_logger.py`.
- All major events (ride requests, assignments, completions, etc.) are logged.
- Logs are written to both console and a file (`myuber.log`).

### 10. Error Handling

- gRPC error codes are used to handle various error scenarios (e.g., ride not found, driver not assigned).
- Try-except blocks are used to catch and log RPC errors in client and driver code.

## Additional Features

### 1. gRPC Interceptors

- Implemented in `myuber_interceptors.py`.
- Used for additional server-side logic, such as logging incoming requests.

### 2. Unique Identifiers

- UUID is used to generate unique ride IDs.

### 3. Thread-Safe Operations

- Queue and threading mechanisms are used to ensure thread-safe operations in the server.

## Conclusion

The MyUber system successfully implements all required functionalities of a basic ride-sharing service. It demonstrates secure, concurrent, and robust handling of ride requests, driver assignments, and ride completions. The system's modular design allows for easy extensions and modifications.

