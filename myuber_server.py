import grpc
from concurrent import futures
import time
import uuid
import queue
import threading
import myuber_pb2
import myuber_pb2_grpc
from myuber_interceptors import get_interceptors
from myuber_logger import logger

class DriverManager:
    def __init__(self):
        # Queue to store available drivers
        self.available_drivers = queue.Queue()
        self.lock = threading.Lock()

    def add_available_driver(self, driver_id):
        # Add a driver to the available drivers queue
        self.available_drivers.put(driver_id)

    def assign_driver(self):
        # Attempt to get an available driver
        try:
            return self.available_drivers.get_nowait()
        except queue.Empty:
            return None

    def get_available_drivers_count(self):
        # Return the number of available drivers
        return self.available_drivers.qsize()

    def register_driver(self, driver_id):
        # Register a new driver
        self.add_available_driver(driver_id)
        return True

class MyUberServicer(myuber_pb2_grpc.RideSharingServicer):
    def __init__(self):
        self.driver_manager = DriverManager()
        self.rides = {}  # Store ride information
        self.ride_queue = queue.Queue()  # Queue for pending rides
        # Start a thread to allocate rides
        self.ride_allocation_thread = threading.Thread(target=self.allocate_rides)
        self.ride_allocation_thread.daemon = True
        self.ride_allocation_thread.start()
        self.ride_timers = {}  # Store timers for ride timeouts

    def allocate_rides(self):
        # Continuously allocate rides to available drivers
        while True:
            ride_id = self.ride_queue.get()
            while True:
                assigned_driver = self.driver_manager.assign_driver()
                if assigned_driver:
                    self.rides[ride_id]["driver_id"] = assigned_driver
                    self.rides[ride_id]["status"] = "DRIVER_ASSIGNED"
                    logger.info(f"Driver {assigned_driver} assigned to ride {ride_id}")
                    
                    # Start a timer for this ride
                    self.start_ride_timer(ride_id, assigned_driver)
                    break
                time.sleep(1)  # Wait for 1 second before trying again
            self.ride_queue.task_done()

    def start_ride_timer(self, ride_id, driver_id):
        # Start a timer for ride acceptance
        timer = threading.Timer(10.0, self.handle_ride_timeout, args=[ride_id, driver_id])
        self.ride_timers[ride_id] = timer
        timer.start()

    def handle_ride_timeout(self, ride_id, driver_id):
        # Handle ride timeout if not accepted within 10 seconds
        if ride_id in self.rides and self.rides[ride_id]["status"] == "DRIVER_ASSIGNED":
            logger.info(f"Ride {ride_id} timed out for driver {driver_id}")
            self.rides[ride_id]["status"] = "REJECTED"
            self.rides[ride_id]["driver_id"] = None
            self.driver_manager.add_available_driver(driver_id)
            self.ride_queue.put(ride_id)

    def RequestRide(self, request, context):
        # Handle a new ride request
        ride_id = str(uuid.uuid4())
        logger.info(f"New ride request: {ride_id} from rider {request.rider_id}")
        self.rides[ride_id] = {
            "status": "PENDING",
            "rider_id": request.rider_id,
            "driver_id": None
        }
        self.ride_queue.put(ride_id)
        return myuber_pb2.RideResponse(ride_id=ride_id, status="PENDING")

    def GetRideStatus(self, request, context):
        # Get the status of a specific ride
        ride_id = request.ride_id
        if ride_id not in self.rides:
            logger.warning(f"Ride {ride_id} not found")
            context.abort(grpc.StatusCode.NOT_FOUND, "Ride not found")

        ride = self.rides[ride_id]
        logger.info(f"Status request for ride {ride_id}: {ride['status']}")
        return myuber_pb2.RideStatusResponse(
            ride_id=ride_id,
            status=ride["status"],
            driver_id=ride["driver_id"] or ""
        )

    def AcceptRide(self, request, context):
        # Handle a driver accepting a ride
        ride_id = request.ride_id
        driver_id = request.driver_id

        if ride_id not in self.rides:
            logger.warning(f"Ride {ride_id} not found during acceptance")
            context.abort(grpc.StatusCode.NOT_FOUND, "Ride not found")

        if self.rides[ride_id]["driver_id"] != driver_id:
            logger.warning(f"Driver {driver_id} not assigned to ride {ride_id}")
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Driver not assigned to this ride")

        # Cancel the timer for this ride
        if ride_id in self.ride_timers:
            self.ride_timers[ride_id].cancel()
            del self.ride_timers[ride_id]

        self.rides[ride_id]["status"] = "ACCEPTED"
        logger.info(f"Ride {ride_id} accepted by driver {driver_id}")
        return myuber_pb2.AcceptRideResponse(success=True, message="Ride accepted")

    def RejectRide(self, request, context):
        # Handle a driver rejecting a ride
        ride_id = request.ride_id
        driver_id = request.driver_id

        if ride_id not in self.rides:
            logger.warning(f"Ride {ride_id} not found during rejection")
            context.abort(grpc.StatusCode.NOT_FOUND, "Ride not found")

        if self.rides[ride_id]["driver_id"] != driver_id:
            logger.warning(f"Driver {driver_id} not assigned to ride {ride_id}")
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Driver not assigned to this ride")

        # Cancel the timer for this ride
        if ride_id in self.ride_timers:
            self.ride_timers[ride_id].cancel()
            del self.ride_timers[ride_id]

        self.rides[ride_id]["status"] = "REJECTED"
        self.rides[ride_id]["driver_id"] = None
        self.driver_manager.add_available_driver(driver_id)
        self.ride_queue.put(ride_id)
        logger.info(f"Ride {ride_id} rejected by driver {driver_id}")
        return myuber_pb2.RejectRideResponse(success=True, message="Ride rejected")

    def CheckForRide(self, request, context):
        # Check if a driver has been assigned a ride
        driver_id = request.driver_id
        for ride_id, ride in self.rides.items():
            if ride['status'] == 'DRIVER_ASSIGNED' and ride['driver_id'] == driver_id:
                return myuber_pb2.CheckRideResponse(has_ride=True, ride_id=ride_id)
        return myuber_pb2.CheckRideResponse(has_ride=False)

    def CompleteRide(self, request, context):
        # Handle ride completion
        ride_id = request.ride_id
        driver_id = request.driver_id

        if ride_id not in self.rides:
            logger.warning(f"Ride {ride_id} not found during completion")
            context.abort(grpc.StatusCode.NOT_FOUND, "Ride not found")

        if self.rides[ride_id]["driver_id"] != driver_id:
            logger.warning(f"Driver {driver_id} not assigned to ride {ride_id}")
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Driver not assigned to this ride")

        self.rides[ride_id]["status"] = "COMPLETED"
        self.driver_manager.add_available_driver(driver_id)
        logger.info(f"Ride {ride_id} completed by driver {driver_id}")
        return myuber_pb2.RideCompletionResponse(success=True, message="Ride completed")

    def RegisterDriver(self, request, context):
        # Register a new driver
        driver_id = request.driver_id
        success = self.driver_manager.register_driver(driver_id)
        if success:
            logger.info(f"Driver {driver_id} registered successfully")
            return myuber_pb2.DriverRegistrationResponse(success=True, message="Driver registered successfully")
        else:
            logger.warning(f"Failed to register driver {driver_id}")
            return myuber_pb2.DriverRegistrationResponse(success=False, message="Failed to register driver")

def serve():
    # Set up SSL credentials for the server
    server_credentials = grpc.ssl_server_credentials(
        [(open('server.key', 'rb').read(), open('server.crt', 'rb').read())],
        root_certificates=open('ca.crt', 'rb').read(),
        require_client_auth=True
    )
    # Create a gRPC server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=get_interceptors()
    )
    # Add the MyUber service to the server
    myuber_pb2_grpc.add_RideSharingServicer_to_server(MyUberServicer(), server)
    # Add a secure port with SSL credentials
    server.add_secure_port('[::]:50051', server_credentials)
    # Start the server
    server.start()
    print("MyUber Server started on port 50051 (SSL enabled)")
    print("Press Ctrl+C to stop the server")
    try:
        # Keep the server running
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        # Stop the server on keyboard interrupt
        server.stop(0)
        print("Server stopped")

if __name__ == '__main__':
    serve()
