import grpc
import myuber_pb2
import myuber_pb2_grpc
from myuber_logger import logger
import time
import threading

class MyUberDriver:
    def __init__(self, driver_id, target='localhost:50051'):
        self.driver_id = driver_id
        # Load SSL certificates
        with open('ca.crt', 'rb') as f:
            root_certificates = f.read()
        with open('client.key', 'rb') as f:
            private_key = f.read()
        with open('client.crt', 'rb') as f:
            certificate_chain = f.read()

        # Create SSL credentials
        credentials = grpc.ssl_channel_credentials(
            root_certificates=root_certificates,
            private_key=private_key,
            certificate_chain=certificate_chain
        )
        # Establish a secure channel to the server
        self.channel = grpc.secure_channel(target, credentials)
        # Create a stub (client) for the RideSharing service
        self.stub = myuber_pb2_grpc.RideSharingStub(self.channel)
        self.current_ride_id = None

    def register_driver(self):
        # Log the driver registration attempt
        logger.info(f"Registering driver {self.driver_id}")
        # Create a DriverRegistrationRequest message
        request = myuber_pb2.DriverRegistrationRequest(driver_id=self.driver_id)
        try:
            # Send the registration request to the server
            response = self.stub.RegisterDriver(request)
            logger.info(f"Driver registration response: {response}")
            return response
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred: {e}")
            return None

    def accept_ride(self, ride_id):
        # Log the ride acceptance attempt
        logger.info(f"Driver {self.driver_id} accepting ride {ride_id}")
        # Create an AcceptRideRequest message
        request = myuber_pb2.AcceptRideRequest(ride_id=ride_id, driver_id=self.driver_id)
        try:
            # Send the accept ride request to the server
            response = self.stub.AcceptRide(request)
            logger.info(f"Ride acceptance response: {response}")
            self.current_ride_id = ride_id
            return response
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred: {e}")
            return None

    def reject_ride(self, ride_id):
        # Log the ride rejection attempt
        logger.info(f"Driver {self.driver_id} rejecting ride {ride_id}")
        # Create a RejectRideRequest message
        request = myuber_pb2.RejectRideRequest(ride_id=ride_id, driver_id=self.driver_id)
        try:
            # Send the reject ride request to the server
            response = self.stub.RejectRide(request)
            logger.info(f"Ride rejection response: {response}")
            return response
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred: {e}")
            return None

    def complete_ride(self):
        if not self.current_ride_id:
            logger.warning("No ride assigned to complete")
            return None

        # Log the ride completion attempt
        logger.info(f"Driver {self.driver_id} completing ride {self.current_ride_id}")
        # Create a RideCompletionRequest message
        request = myuber_pb2.RideCompletionRequest(ride_id=self.current_ride_id, driver_id=self.driver_id)
        try:
            # Send the complete ride request to the server
            response = self.stub.CompleteRide(request)
            logger.info(f"Ride completion response: {response}")
            self.current_ride_id = None
            return response
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred: {e}")
            return None

    def check_for_ride(self):
        try:
            # Send a request to check for assigned rides
            response = self.stub.CheckForRide(myuber_pb2.CheckRideRequest(driver_id=self.driver_id))
            return response.ride_id if response.has_ride else None
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred while checking for ride: {e}")
            return None

def run_driver():
    # Get the driver ID from user input
    driver_id = input("Enter your driver ID: ")
    driver = MyUberDriver(driver_id)
    
    # Register the driver
    registration_response = driver.register_driver()
    if not registration_response or not registration_response.success:
        print("Failed to register driver. Exiting.")
        return

    print(f"Driver {driver_id} registered successfully.")

    while True:
        print("\nChecking for ride assignment...")
        ride_id = driver.check_for_ride()
        
        if ride_id:
            print(f"Ride {ride_id} assigned. You have 10 seconds to accept.")
            
            def timed_input():
                choice[0] = input("Enter 'a' to accept or 'r' to reject: ")

            choice = [None]
            # Start a thread to get user input with a timeout
            input_thread = threading.Thread(target=timed_input)
            input_thread.start()
            input_thread.join(timeout=10)

            if choice[0] is None:
                print("\nTime's up! Ride automatically rejected.")
                # Don't attempt to reject the ride here, as it's already been handled by the server
            elif choice[0].lower() == 'a':
                response = driver.accept_ride(ride_id)
                if response and response.success:
                    print("Ride accepted. Waiting for completion...")
                    while True:
                        complete = input("Enter 'c' when the ride is completed: ")
                        if complete.lower() == 'c':
                            complete_response = driver.complete_ride()
                            if complete_response and complete_response.success:
                                print("Ride completed successfully.")
                                break
                            else:
                                print("Failed to complete ride. Please try again.")
                        else:
                            print("Invalid input. Please enter 'c' to complete the ride.")
                else:
                    print("Failed to accept ride. It may have been reassigned.")
            elif choice[0].lower() == 'r':
                response = driver.reject_ride(ride_id)
                if response and response.success:
                    print("Ride rejected successfully.")
                else:
                    print("Failed to reject ride. It may have been automatically rejected.")
            else:
                print("Invalid choice. Ride may be reassigned.")
        else:
            print("No ride assigned. Waiting...")
        
        time.sleep(5)  # Wait for 5 seconds before checking again

if __name__ == '__main__':
    run_driver()
