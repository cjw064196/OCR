# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""Simple HTTP Server With Upload.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""


__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]

import os
import posixpath
import BaseHTTPServer
import urllib
import cgi
import shutil
import mimetypes
import re
import json
import time
from log import *
#from recognize import *


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        logger.info("%s, %s by: %s", r, info, self.client_address)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({'result': info, 'success': r}))
       
    def deal_post_data(self):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type') or '')
        if not pdict:
            return (False, "Content NOT begin with boundary")
        postvars = cgi.parse_multipart(self.rfile, pdict)
        if not postvars.get('file'):
            return (False, "Can't find out file ...")
        if not postvars.get('project'):
            return (False, "Can't find out project ...")

        file_content = postvars.get('file')[0]
        project = postvars.get('project')[0]
        if project not in ['ipe', 'wenshu', 'lvwang']:
            return (False, "Unknown project ...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, "uploads", project, repr(float(time.time())) + '.png')

        directory = os.path.dirname(fn)
        if not os.path.exists(directory):
            os.makedirs(directory)
        #logger.info(fn)  # fn -> 文件最终存储位置

        try:
            out = open(fn, 'wb')
            out.write(file_content)
            out.close()
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")

        try:
            mod_name = "recognize." + project
            mod = __import__(mod_name, fromlist=['*'])
            text, image = mod.captcha_text_and_image(fn)
            predict_text = mod.crack_captcha(image)
            return (True, predict_text)
        except Exception, e:
            return (False, repr(e))

    '''
    send_head 方法通过uri的path分析得到客户请求的网路路径。构造head的mime元信息并发送到客户端，然后返回一个打开path的文件句柄。
    '''
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
    '''
    SimpleHTTPServer模块还提供了list_directory方法，用于响应path是一个目录，而不是文件的情况。
    '''
    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Please browse and upload captcha %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Please browse and upload captcha %s</h2>\n" % displaypath)
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\"/>")
        f.write("<p>Project: <input name=\"project\" type=\"text\" value=\"ipe\"/></p>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write("<hr>\n<ul>\n")
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)rfile

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
    '''
    do_GET的下一步就是通过 copyfile方法，将客户请求的path的文件数据写入到缓冲可写文件中，发送给客户端。
    '''
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })


def test(HandlerClass = SimpleHTTPRequestHandler,
         ServerClass = BaseHTTPServer.HTTPServer):
    BaseHTTPServer.test(HandlerClass, ServerClass)

if __name__ == '__main__':
    test()
