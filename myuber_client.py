import grpc
import myuber_pb2
import myuber_pb2_grpc
from myuber_logger import logger
import time

class MyUberClient:
    def __init__(self, target='localhost:50051'):
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

    def request_ride(self, rider_id):
        # Log the ride request
        logger.info(f"Requesting ride for rider {rider_id}")
        # Create a RideRequest message
        request = myuber_pb2.RideRequest(rider_id=rider_id)
        try:
            # Send the ride request to the server
            response = self.stub.RequestRide(request)
            logger.info(f"Ride request response: {response}")
            return response
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred: {e}")
            return None

    def get_ride_status(self, ride_id):
        # Log the status request
        logger.info(f"Getting status for ride {ride_id}")
        # Create a RideStatusRequest message
        request = myuber_pb2.RideStatusRequest(ride_id=ride_id)
        try:
            # Send the status request to the server
            response = self.stub.GetRideStatus(request)
            logger.info(f"Ride status: {response}")
            return response
        except grpc.RpcError as e:
            # Log any RPC errors
            logger.error(f"RPC error occurred: {e}")
            return None

def run_client():
    # Create a client instance
    client = MyUberClient()
    # Get the rider ID from user input
    rider_id = input("Enter your rider ID: ")
    
    # Request a ride
    response = client.request_ride(rider_id)
    if response:
        ride_id = response.ride_id
        print(f"Ride requested. Ride ID: {ride_id}")
        
        # Continuously check ride status
        while True:
            status = client.get_ride_status(ride_id)
            if status:
                print(f"Ride status: {status.status}")
                if status.status == "COMPLETED":
                    print("Ride completed. Exiting.")
                    break
                elif status.status == "DRIVER_ASSIGNED":
                    print(f"Driver assigned: {status.driver_id}")
                elif status.status == "REJECTED":
                    print("Ride was rejected by the driver. Requesting a new ride...")
                    # Request a new ride if the current one was rejected
                    response = client.request_ride(rider_id)
                    if response:
                        ride_id = response.ride_id
                        print(f"New ride requested. Ride ID: {ride_id}")
                    else:
                        print("Failed to request a new ride. Exiting.")
                        break
            time.sleep(5)  # Wait for 5 seconds before checking again

if __name__ == '__main__':
    run_client()
