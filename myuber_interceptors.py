import grpc
from myuber_logger import logger

class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        # Log incoming requests
        logger.info(f"Received request: {handler_call_details.method}")
        # Continue with the normal request processing
        return continuation(handler_call_details)

def get_interceptors():
    # Return a list of interceptors to be used by the server
    return [LoggingInterceptor()]
