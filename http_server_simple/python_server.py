import socket
import socketserver
from http.server import SimpleHTTPRequestHandler
import os
import urllib.parse
import json
import zipfile
import io

# ==================== CONFIGURATION ====================
# Set the directory you want to serve
# Examples:
#   SERVE_DIRECTORY = r"D:\Videos"
#   SERVE_DIRECTORY = r"C:\Users\YourName\Documents"
#   SERVE_DIRECTORY = r"E:\Movies"
#   SERVE_DIRECTORY = "."  # Current directory
SERVE_DIRECTORY = r"D:\Videos"
# =======================================================

class MyHandler(SimpleHTTPRequestHandler):
    
    def do_POST(self):
        """Handle POST requests for zip downloads"""
        if self.path == '/download-zip':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                file_list = data.get('files', [])
                if not file_list:
                    self.send_error(400, "No files specified")
                    return
                
                print(f"Received request to zip {len(file_list)} files")
                
                                # ------------------------------------------------------------
                #  CREATE ZIP FILE IN MEMORY   (fixed – copy‑paste this block)
                # ------------------------------------------------------------
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_info in file_list:
                        # ---- 1️⃣  Skip directories ---------------------------------
                        if file_info.get('isDir', False):
                            continue

                        # ---- 2️⃣  Get the href the UI sent (e.g. "subdir/video.mp4")
                        href = file_info.get('href', '')
                        if not href:
                            continue

                        # ---- 3️⃣  Decode it and build an absolute path yourself -----
                        #      No call to self.translate_path – we concatenate only once.
                        decoded_href = urllib.parse.unquote(href).lstrip('/')      # "subdir/video.mp4"
                        # Normalise OS‑specific separators (Windows uses back‑slashes)
                        normalized_rel = decoded_href.replace('/', os.sep)
                        full_path = os.path.abspath(os.path.join(SERVE_DIRECTORY, normalized_rel))

                        # ---- 4️⃣  Security check – must stay inside SERVE_DIRECTORY --
                        base = os.path.abspath(SERVE_DIRECTORY)
                        if os.path.commonpath([full_path, base]) != base:
                            print(f"🔒 Blocked outside‑root access: {full_path}")
                            continue

                        # ---- 5️⃣  Does the file really exist? ----------------------
                        if not os.path.isfile(full_path):
                            print(f"⚠️ File not found (skipped): {full_path}")
                            continue

                        # ---- 6️⃣  Add it to the zip -------------------------------
                        arcname = file_info.get('name', os.path.basename(full_path))
                        print(f"📦 Adding to zip: {arcname}  ← {full_path}")
                        zip_file.write(full_path, arcname)

                # ------------------------------------------------------------
                #  GET ZIP DATA (unchanged)
                # ------------------------------------------------------------
                zip_data = zip_buffer.getvalue()

                
                if len(zip_data) < 100:  # Empty or nearly empty zip
                    self.send_error(400, "No valid files to zip")
                    return
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                self.send_header('Content-Disposition', 'attachment; filename="files.zip"')
                self.send_header('Content-Length', str(len(zip_data)))
                self.end_headers()
                self.wfile.write(zip_data)
                print(f"✅ Successfully sent zip file ({len(zip_data)} bytes)")
                
            except Exception as e:
                print(f"❌ Error creating zip: {e}")
                import traceback
                traceback.print_exc()
                try:
                    self.send_error(500, f"Error creating zip: {str(e)}")
                except:
                    pass
        else:
            self.send_error(404, "Not found")
    
    #....
    #def translate_path(self, path):
    #    """Override to serve from custom directory"""
        # Get the path relative to root
    #    path = super().translate_path(path)
        # Get relative path from current directory
    #    relpath = os.path.relpath(path, os.getcwd())
        # Return path in our custom directory
    #    return os.path.join(SERVE_DIRECTORY, relpath)
    
    def list_directory(self, path):
        """Custom directory listing with modern UI"""
        try:
            list_dir = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
        
        list_dir.sort(key=lambda a: a.lower())
        
        # Build file list data
        files_data = []
        for name in list_dir:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            
            # Append / for directories
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            
            # Get file size
            size = 0
            if not os.path.isdir(fullname):
                try:
                    size = os.path.getsize(fullname)
                except:
                    size = 0
            
            files_data.append({
                'name': displayname.rstrip('/'),
                'href': urllib.parse.quote(linkname, errors='surrogatepass'),
                'isDir': os.path.isdir(fullname),
                'size': size
            })
        
        # Load UI template from external file
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'ui_template.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        except FileNotFoundError:
            self.send_error(500, "UI template file 'ui_template.html' not found")
            return None
        except Exception as e:
            self.send_error(500, f"Error loading UI template: {str(e)}")
            return None
        
        # Inject file data into template
        html = html_template.replace('__FILES_DATA__', json.dumps(files_data))
        
        encoded = html.encode('utf-8', 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None
    
    def end_headers(self):
        # Add headers to better support video streaming
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()
    
    def copyfile(self, source, outputfile):
        """Override to handle connection resets gracefully"""
        try:
            # Use smaller buffer for better handling of interruptions
            buffer_size = 64 * 1024  # 64KB chunks
            while True:
                buf = source.read(buffer_size)
                if not buf:
                    break
                try:
                    outputfile.write(buf)
                except (ConnectionResetError, BrokenPipeError):
                    # Client disconnected (normal for video streaming - browser preflight)
                    return
        except Exception as e:
            print(f"Error during file transfer: {e}")

PORT = 8080

# Validate and set the serve directory
if not os.path.exists(SERVE_DIRECTORY):
    print(f"ERROR: Directory '{SERVE_DIRECTORY}' does not exist!")
    exit(1)

if not os.path.isdir(SERVE_DIRECTORY):
    print(f"ERROR: '{SERVE_DIRECTORY}' is not a directory!")
    exit(1)

print(f"Serving directory: {os.path.abspath(SERVE_DIRECTORY)}")
print(f"Server running on port {PORT}")
print(f"Make sure 'ui_template.html' is in the same directory as this script")

# Set SO_REUSEADDR to avoid "address already in use" errors
socketserver.TCPServer.allow_reuse_address = True

httpd = socketserver.TCPServer(("", PORT), MyHandler)

# Enable TCP keepalive
httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

# Optional: Set TCP keepalive parameters (Windows)
try:
    httpd.socket.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 3000))
except AttributeError:
    pass  # Not on Windows or not supported

print("-" * 50)
print(f"🚀 Server is ready!")
print(f"📁 Access your files at: http://localhost:{PORT}")
print(f"📂 Serving: {os.path.abspath(SERVE_DIRECTORY)}")
print("-" * 50)

httpd.serve_forever()