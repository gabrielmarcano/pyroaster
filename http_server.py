import socket
import sys
import io
import json
import logger

HTTP_CODES = {
    100: "Continue",
    200: "OK",
    201: "Created",
    304: "Not Modified",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
    # Add more as needed
}


class HttpServer:
    def __init__(self, host="0.0.0.0", port=80):
        """Initialize the server with host and port."""
        self.host = host
        self.port = port
        self.routes = {}
        self.socket = None
        self.connection = None
        self.logger = logger.SimpleLogger()
        self.sse_clients = []
        self.event_id = 0

    def start(self):
        """Start the HTTP server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.logger.info(f"Server started at {self.host}:{self.port}")

        try:
            while True:
                try:
                    self.connection, address = self.socket.accept()
                    request = self.get_request()
                    if not request:
                        continue
                    self.handle_request(request)
                except Exception as e:
                    self.handle_error(e)
                finally:
                    if self.connection not in self.sse_clients:
                        self.connection.close()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the server."""
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
        self.logger.info("Server stopped")

    def add_route(self, path, handler, methods=["GET"]):
        """Add a route to the server with one or more methods."""
        for method in methods:
            if method not in self.routes:
                self.routes[method] = []
            self.routes[method].append({"path": path, "handler": handler})

    def find_route_for_path(self, path):
        """Find a route matching the path (ignoring method)."""
        try:
            resources = path.split("/")[1:]
            root = f"/{resources[0]}"
        except IndexError:
            root = "/"

        for method_routes in self.routes.values():
            for route in method_routes:
                if route["path"] == root:
                    return route
        return None

    def get_request(self, buffer_length=4096):
        """Retrieve the request body."""
        return self.connection.recv(buffer_length).decode("utf-8")

    def get_request_body(self, request: str):
        """Retrieve the request payload."""
        body_pos = request.find("\r\n\r\n")
        if body_pos == -1:
            return {}
        body_pos += 4
        return request[body_pos:]

    def parse_request(self, request):
        """Parse the request and extract the method and path."""
        lines = request.split("\r\n")
        try:
            method, path = lines[0].split(" ")[:2]
        except (
            AttributeError
        ):  # If the request line is malformed, return None for method/path
            return None, None
        return method, path

    def handle_request(self, request):
        """Handle incoming requests and route them."""
        method, path = self.parse_request(request)
        if method is None or path is None:
            self.handle_bad_request(request)  # 400 for malformed requests
            return

        # Find a route for the path (ignoring method for now)
        route = self.find_route_for_path(path)

        # If no route is found for the path, send 404 Not Found
        if route is None:
            self.handle_route_not_found(request)

        else:
            # If the route is found, check if the method is allowed
            if route in self.routes.get(method):
                route["handler"](request)  # Call the handler if the method is allowed
            else:
                self.handle_method_not_allowed(
                    method, request
                )  # Handle method not allowed

    def format_exception(self, exc):
        """Format exception for logging."""
        output = io.StringIO()
        sys.print_exception(exc, output)
        return output.getvalue()

    def handle_error(self, error):
        """Handle 500 internal server errors."""
        error_message = (
            str(error)
            if not hasattr(sys, "print_exception")
            else self.format_exception(error)
        )
        self.send_response(f"Internal Server Error: {error_message}", http_code=500)
        self.logger.error(error_message)

    def handle_bad_request(self, request):
        """Handle a 400 bad request error."""
        self.send_response("Bad Request", http_code=400)
        self.logger.warning(f"Bad request for {request}")

    def handle_route_not_found(self, request):
        """Handle a 404 route not found error."""
        self.send_response("Not found", http_code=404)
        self.logger.warning(f"Route not found for {request}")

    def handle_method_not_allowed(self, method, request):
        """Handle a 405 method not allowed error."""
        self.send_response(f"Method {method} Not Allowed", http_code=405)
        self.logger.warning(f"Method {method} Not Allowed for {request}")

    def handle_sse(self, request):
        """SSE Handler"""
        headers = [
            "Cache-Control: no-cache",
            "Access-Control-Allow-Origin: *",
            "Connection: keep-alive",
            "Retry-After: 5",  # Optional: to suggest reconnection delay
        ]

        self.send_response(
            "", http_code=200, content_type="text/event-stream", extend_headers=headers
        )
        self.sse_clients.append(self.connection)  # Add the client to the list
        self.logger.info(f"New SSE client connected: {self.connection}")

    def send(self, data):
        """Send data to the client."""
        if self.connection:
            self.connection.sendall(data.encode())

    def send_response(
        self, body, http_code=200, content_type="text/plain", extend_headers=None
    ):
        """Send an HTTP response."""
        headers = [
            f"HTTP/1.1 {http_code} {HTTP_CODES.get(http_code)}",
            f"Content-Type: {content_type}",
        ]

        # Add any additional headers if provided
        if extend_headers:
            headers.extend(extend_headers)

        self.send("\r\n".join(headers) + "\r\n\r\n" + body)

    def send_sse(self, data, event=None):
        """Send SSE data to all connected clients"""
        # Increment event ID for each message
        self.event_id += 1

        # Convert data to JSON if it's a dictionary or list
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)

        sse_data = "id: {}\ndata: {}\n\n".format(self.event_id, data_str)
        if event:
            sse_data = "event: {}\n".format(event) + sse_data

        disconnected_clients = []
        for client in self.sse_clients:
            try:
                client.sendall(sse_data.encode())
            except Exception as e:
                self.logger.error(f"Error sending to client {client}: {e}")
                disconnected_clients.append(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.sse_clients.remove(client)
            self.logger.info(f"Client disconnected: {client}")
