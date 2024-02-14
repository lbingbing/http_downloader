import http.server

def get_file_bytes(size):
    return bytes([i & 0xff for i in range(size)])

class Handler(http.server.BaseHTTPRequestHandler):
    file_size = 1024

    def do_GET(self):
        file_content = get_file_bytes(self.file_size)
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Content-Length', str(len(file_content)))
        self.end_headers()
        self.wfile.write(file_content)

def start_file_server(port, file_size):
    Handler.file_size = file_size
    with http.server.HTTPServer(('', port), Handler) as httpd:
        print('start serving')
        httpd.handle_request()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help='http file server port')
    parser.add_argument('file_size', type=int, help='file size')
    args = parser.parse_args()

    start_file_server(args.port, args.file_size)
