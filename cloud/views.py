from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from wsgiref.util import FileWrapper
from .models import CloudUser
import hashlib
# from django.core import serializers
import os, json, mimetypes, shutil
from django.core.files.storage import FileSystemStorage

class FixedFileWrapper(FileWrapper):
    def __iter__(self):
        self.filelike.seek(0)
        return self

# Create your views here.

def index(request):
    # if user already logged in
    if 'user' in request.session:
        return render(request, 'cloud/index.html', {'inSession': True,
                                                    'user': request.session['user']['displayName']})
    else:
        return render(request, 'cloud/index.html', {'inSession': False})

def login(request):
    if request.method == 'POST':
        # Check credentials
        try:
            user = CloudUser.objects.get(username=str(request.POST.get('username', '')))
        # If username not found
        except CloudUser.DoesNotExist:
            return HttpResponseRedirect('/cloud/')
        else:
            hasher = hashlib.md5()
            byteString = str(request.POST.get('password', '')).encode('utf-8')
            hasher.update(byteString)
            hashedPassword = hasher.hexdigest()

            # If password mathces
            if user.password == hashedPassword:
                # Save user in session
                # dbconvertion = serializers.serialize('json', [user])
                # # dbconversion example: [{"model": "cloud.clouduser", "pk": 1,
                # # "fields": {"username": "omersaar", "password": "615cbd3c12ae35ef0068c6aa0aef606c",
                # # "displayName": "Omer Saar", "directory": "NULL"}}]
                # struct = json.loads(dbconvertion)
                # userJson = json.dumps(struct[0])
                request.session['user'] = {
                    'username': user.username,
                    'displayName': user.displayName,
                    'directory': user.directory
                }
                return HttpResponseRedirect('/cloud/userPage')
            else:
                return HttpResponseRedirect('/cloud/')
    else:
        return HttpResponseRedirect('/cloud/')

def userPage(request):
    if 'user' in request.session:
        if 'uploaded' in request.session:
            was_uploaded = request.session['uploaded']
            del request.session['uploaded']
            return render(request, 'cloud/userPage.html', {'displayName': request.session['user']['displayName'],
                                                           'username': request.session['user']['username'],
                                                           'uploaded': True,
                                                           'successfully': was_uploaded})
        else:
            return render(request, 'cloud/userPage.html', {'displayName': request.session['user']['displayName'],
                                                           'username': request.session['user']['username']})
    else:
        return HttpResponseRedirect('/cloud/')

@csrf_exempt
def filesInDir(request):
    # If a session exsits
    if 'user' in request.session:
        # If the method is POST
        if request.method == 'POST':
            base_dir = request.session['user']['directory']
            drive, base_dir = os.path.splitdrive(base_dir)
            route = str(json.loads(request.body.decode())['route'])

            # Security check
            try:
                nRoute = checkRoute(route)

                fullPath = os.path.join(base_dir, nRoute)

                if 'back' in json.loads(request.body.decode()):
                    if nRoute != "":
                        fullPath = os.path.split(fullPath)[0]

                fullPath = drive + fullPath

                # If the path given is a directory
                if os.path.isdir(fullPath):
                    files = os.listdir(fullPath)

                    data = []
                    for file in files:
                        # file contains only the name of the file, not the full path
                        fileData = {}
                        fileData['name'] = file

                        if os.path.isfile(os.path.join(fullPath, file)):
                            fileData['type'] = file.split('.')[-1]
                        else:
                            fileData['type'] = 'directory'

                        fileData['size'] = os.path.getsize(os.path.join(fullPath, file)) / 1000
                        data.append(fileData)

                    dataWrapper = {}
                    dataWrapper['files'] = data

                    if 'back' in json.loads(request.body.decode()):
                        dataWrapper['route'] = os.path.split(nRoute)[0]
                    return JsonResponse(dataWrapper)
                else:
                    return HttpResponseBadRequest('Not a directory')
            # In case of suspected security breach attempt
            except ValueError as e:
                return HttpResponse('Nice try')
        else:
            return HttpResponseBadRequest('POST method')
    else:
        return HttpResponse('Log in at /cloud')

# A function that gets a route, checks for security breaches and returns a normpath
# throws ValueError exception in case of suspecting security breach attempt
def checkRoute(route):
    # Security check
    nRoute = os.path.normpath(route)

    if nRoute == "" or nRoute == "\\":
        nRoute = ""
    else:
        if nRoute[0] == '\\':
            nRoute = nRoute[1:]

        a = nRoute.split('\\')

        for directory in a:
            if directory == '..':
                nRoute = ""
                raise ValueError("Trying to breech security")
    return nRoute

@csrf_exempt
def createNewDirectory(request):
    # If a user is logged in
    if 'user' in request.session:
        # If the method is POST
        if request.method == 'POST':
            base_dir = request.session['user']['directory']
            drive, base_dir = os.path.splitdrive(base_dir)
            route = str(json.loads(request.body.decode())['route'])
            new_dir_name = str(json.loads(request.body.decode())['dirname'])

            # Make sure new_dir_name is not empty
            if new_dir_name == "":
                return HttpResponseBadRequest('The name cannot be empty')

            # Security check
            try:
                nRoute = checkRoute(route)

                fullPath = os.path.join(base_dir, nRoute)

                fullPath = drive + fullPath

                # If the path given is a directory
                if os.path.isdir(fullPath):
                    # Check if new_dir_name is a valid directory name
                    if isObjectNameValid(new_dir_name):
                        new_dir_path = os.path.join(fullPath, new_dir_name)

                        # Check if the name is not already taken
                        if not os.path.exists(new_dir_path):
                            os.makedirs(new_dir_path)
                            return HttpResponse('Directory created successfully!')
                        else:
                            return HttpResponseBadRequest('The directory name is already taken')
                    else:
                        return HttpResponseBadRequest('The directory name cannot contain: \ / * ? : | " < >')
                else:
                    return HttpResponseBadRequest('Not a directory')
            except ValueError as e:
                return HttpResponse('Nice try')
        else:
            return HttpResponseBadRequest('POST method')
    else:
        return HttpResponse('Log in at /cloud')

def isObjectNameValid(objname):
    forbidden = ('\\', '/', '?', '*', ':', '<', '>', '|', '\"')

    for f in forbidden:
        if f in objname:
            return False

    return True

@csrf_exempt
def setFile(request):
    if 'user' in request.session:
        if request.method == 'POST':
            base_dir = request.session['user']['directory']
            dir_of_file = str(json.loads(request.body.decode())['route'])
            filename = str(json.loads(request.body.decode())['filename'])

            try:
                nRoute = checkRoute(dir_of_file)

                # Security check for file name
                if isObjectNameValid(filename):
                    fullpath = os.path.join(base_dir, dir_of_file)
                    fullpath_file = os.path.join(fullpath, filename)
                    request.session['download_file_path'] = fullpath_file
                    return HttpResponse('File saved')
                else:
                    return HttpResponseBadRequest('Invalid file name')

            except ValueError as e:
                return HttpResponse('Nice try')
        else:
            return HttpResponse('POST method')
    else:
        return HttpResponse('Log in at /cloud')

def getFile(request):
    if 'user' in request.session:
        if 'download_file_path' in request.session:
            fullpath_file = request.session['download_file_path']
            response = HttpResponse(FixedFileWrapper(open(fullpath_file, 'rb')),
                                    content_type=mimetypes.guess_type(fullpath_file)[0])
            response['Content-Length'] = os.path.getsize(fullpath_file)
            response['Content-Disposition'] = "attachment; filename=%s" % os.path.basename(fullpath_file)

            del request.session['download_file_path']
            return response
        else:
            return HttpResponseBadRequest('File not selected')
    else:
        return HttpResponse('Log in at /cloud')

@csrf_exempt
def uploadFile(request):
    if 'user' in request.session:
        if request.method == 'POST' and request.FILES['myfile']:
            nRoute = request.POST['dir']
            myfile = request.FILES['myfile']

            try:
                nRoute = checkRoute(request.POST['dir'])
                base_dir = request.session['user']['directory']
                fs = FileSystemStorage(location=os.path.join(base_dir, nRoute))

                if not fs.exists(myfile.name):
                    fs.save(myfile.name, myfile)

                    request.session['uploaded'] = True
                    return HttpResponseRedirect('/cloud/userPage')
                else:
                    request.session['uploaded'] = False
                    return HttpResponseRedirect('/cloud/userPage')
            except ValueError as e:
                return HttpResponse('Nice try')
        else:
            return HttpResponse('Choose a file to upload by POST')
    else:
        return HttpResponse('Log in at /cloud')

@csrf_exempt
def deleteFile(request):
    if 'user' in request.session:
        if request.method == 'POST':
            route = str(json.loads(request.body.decode())['fileDir'])
            filename = str(json.loads(request.body.decode())['filename'])

            try:
                # Check route
                nRoute = checkRoute(route)

                # Check filename validity
                if isObjectNameValid(filename):
                    base_dir = request.session['user']['directory']
                    fullpath = os.path.join(base_dir, nRoute)
                    fullpath = os.path.join(fullpath, filename)

                    if os.path.isfile(fullpath):
                        os.remove(fullpath)
                        return HttpResponse('File removed successfully')
                    else:
                        return HttpResponseBadRequest('File does not exist')
                else:
                    return HttpResponse('Nice try')
            except ValueError as e:
                return HttpResponse('Nice try')
        else:
            return HttpResponseBadRequest('POST method')
    else:
        return HttpResponse('Log in at /cloud')

@csrf_exempt
def deleteDirectory(request):
    if 'user' in request.session:
        if request.method == 'POST':
            route = str(json.loads(request.body.decode())['route'])
            dirname = str(json.loads(request.body.decode())['dirname'])

            try:
                # Check route
                nRoute = checkRoute(route)

                # Check filename validity
                if isObjectNameValid(dirname):
                    base_dir = request.session['user']['directory']
                    fullpath = os.path.join(base_dir, nRoute)
                    fullpath = os.path.join(fullpath, dirname)

                    if os.path.isdir(fullpath):
                        shutil.rmtree(fullpath)
                        return HttpResponse('Folder removed successfully')
                    else:
                        return HttpResponseBadRequest('Folder does not exist')
                else:
                    return HttpResponse('Nice try')
            except ValueError as e:
                return HttpResponse('Nice try')
        else:
            return HttpResponseBadRequest('POST method')
    else:
        return HttpResponse('Log in at /cloud')

def logout(request):
    if 'user' in request.session:
        del request.session['user']
    return HttpResponseRedirect('/cloud/')

def stam(request, number):
    try:
        user = CloudUser.objects.get(pk=number)
    except CloudUser.DoesNotExist:
        raise Http404("User not found")
    return HttpResponse('<p>' + str(number) + '</p>')