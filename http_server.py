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
    406: "Not Acceptable",
    500: "Internal Server Error",
    # Add more as needed
}


class HttpServer:
    def __init__(self, host="0.0.0.0", port=80):
        """Initialize the server with host and port."""
        self.host = host
        self.port = port
        self.routes: dict[str, list[dict[str, function | str]] | None] = {}
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

    def add_route(self, path: str, handler: function, methods: list[str] = ["GET"]):
        """Add a route to the server with one or more methods."""
        for method in methods:
            if method not in self.routes:
                self.routes[method] = []
            self.routes[method].append({"path": path, "handler": handler})

    def find_route_for_path(self, path: str):
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
        """Retrieve the request."""
        return self.connection.recv(buffer_length).decode("utf-8")

    def get_request_body(self, request: str):
        """Extract the body from the request."""
        body_pos = request.find("\r\n\r\n")
        if body_pos == -1:
            return ""
        body_pos += 4
        return request[body_pos:]

    def get_request_headers(self, request: str):
        """Extract the headers from the request."""
        headers = {}
        lines = request.split("\r\n")
        for line in lines[1:]:
            if ":" in line:
                key, value = line.split(": ", 1)
                headers[key] = value
        return headers

    def parse_request(self, request: str):
        """Parse the request and extract the method and path."""
        lines = request.split("\r\n")
        try:
            method, path = lines[0].split(" ")[:2]
        except (
            AttributeError
        ):  # If the request line is malformed, return None for method/path
            return None, None
        return method, path

    def parse_json_body(self, request: str):
        """Parse the JSON body of the request."""
        body = self.get_request_body(request)
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None

    def handle_request(self, request: str):
        """Handle incoming requests and route them."""
        method, path = self.parse_request(request)
        if method is None or path is None:
            self.handle_bad_request(request)
            return

        route = self.find_route_for_path(path)

        if route is None:
            self.handle_route_not_found(request)

        else:
            if route in self.routes.get(method):
                route["handler"](request)
            else:
                self.handle_method_not_allowed(method, request)

    def format_exception(self, exc: Exception):
        """Format exception for logging."""
        output = io.StringIO()
        sys.print_exception(exc, output)
        return output.getvalue()

    def handle_error(self, error: Exception):
        """Handle 500 internal server errors."""
        error_message = (
            str(error)
            if not hasattr(sys, "print_exception")
            else self.format_exception(error)
        )
        self.send_response(f"Internal Server Error: {error_message}", http_code=500)
        self.logger.error(error_message)

    def handle_bad_request(self, request: str):
        """Handle a 400 bad request error."""
        self.send_response("Bad Request", http_code=400)
        self.logger.warning(f"Bad request for {request}")

    def handle_route_not_found(self, request: str):
        """Handle a 404 route not found error."""
        self.send_response("Not found", http_code=404)
        self.logger.warning(f"Route not found for {request}")

    def handle_method_not_allowed(self, method: str, request: str):
        """Handle a 405 method not allowed error."""
        self.send_response(f"Method {method} Not Allowed", http_code=405)
        self.logger.warning(f"Method {method} Not Allowed for {request}")

    def handle_sse(self, request: str):
        """SSE Handler"""

        request_headers = self.get_request_headers(request)
        if request_headers.get("Accept") != "text/event-stream":
            self.send_response("Not Acceptable", http_code=406)
            return

        headers = [
            "Cache-Control: no-cache",
            "Access-Control-Allow-Origin: *",
            "Connection: keep-alive",
            # "Retry-After: 5",  # Optional: to suggest reconnection delay
        ]

        self.send_response(
            "", http_code=200, content_type="text/event-stream", extend_headers=headers
        )
        self.sse_clients.append(self.connection)
        self.logger.info(f"New SSE client connected: {self.connection}")

    def send(self, data: str):
        """Send data to the client."""
        if self.connection:
            self.connection.sendall(data.encode())

    def send_response(
        self,
        body: str,
        http_code=200,
        content_type="text/plain",
        extend_headers: list[str] | None = None,
    ):
        """Send an HTTP response."""
        headers = [
            f"HTTP/1.1 {http_code} {HTTP_CODES.get(http_code)}",
            f"Content-Type: {content_type}",
        ]

        if content_type != "text/event-stream":
            headers.append(f"Content-Length: {len(body)}")
            headers.append("Connection: close")

        if extend_headers:
            headers.extend(extend_headers)

        self.send("\r\n".join(headers) + "\r\n\r\n" + body)

    def send_sse(self, data: str | dict | list, event: str | None = None):
        """Send SSE data to all connected clients"""
        self.event_id += 1

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

        for client in disconnected_clients:
            self.sse_clients.remove(client)
            self.logger.info(f"Client disconnected: {client}")
