/**
 * Created by omer on 29/10/2016.
 */
app = angular.module('cloudApp', []);

app.controller('mainCtrl', ['$scope', '$http', '$filter', function ($scope, $http, $filter) {
    // Init scope variables
    $scope.currRoute = "";
    $scope.dirname = "";
    $scope.files = [];
    $scope.fileSelectedIndex = -1;
    $scope.fileSelected = null;
    $scope.sortedBy = "";
    $scope.reverseSort = false;

    $scope.objectClickedFlag = false;// To prevent ng-click of outer element <tr>

    // Initial loading of main directory
    loadFiles($scope.currRoute);

    $scope.objectClicked = function (file) {
        $scope.objectClickedFlag = true;
        somethingClicked();
        // If the pressed object is a directory
        if (file.type == "directory") {
            if ($scope.currRoute == "") {
                $scope.currRoute += file.name;
            } else {
                $scope.currRoute += "\\" + file.name;
            }
            loadFiles($scope.currRoute);
        } else { // If the pressed object is a file
            var promise = $http.post('/cloud/files/set', {route: $scope.currRoute, filename: file.name});

            promise.success(function (data) {
                var dElem = document.getElementById('downloadButton2');
                dElem.click();
            }).error(function (data) {
                alert("There has been an issue selecting the file");
            });
        }
    };

    $scope.createNewDir = function () {
        somethingClicked();
        $('#dirnameWarning').html('');
        if ($scope.dirname == "") {
            $('#dirnameWarning').html('The name cannot be empty');
        } else {
            var promise = $http.post('/cloud/dirs/add', {route: $scope.currRoute, dirname: $scope.dirname});

            promise.success(function (data) {
                loadFiles($scope.currRoute);
                $('#add-directory').modal('hide');
            }).error(function (data) {
                $('#dirnameWarning').html(data);
            });
        }
    };

    $scope.goBack = function () {
        somethingClicked();
        var filesPromise = $http.post('/cloud/dirs/files', {route: $scope.currRoute, back: ""});

        filesPromise.success(function (data) {
            $scope.files = data.files;
            $scope.currRoute = data.route;
        });
    };

    $scope.selectRow = function (index, file) {
        if (! $scope.objectClickedFlag) {
            // If selected row was pressed
            if ($scope.fileSelectedIndex == index) {
                $scope.fileSelectedIndex = -1;
                $scope.fileSelected = null;
            } else {
                $scope.fileSelectedIndex = index;
                $scope.fileSelected = file;

                if ($scope.fileSelected.type != 'directory') {
                    $('#downloadButton1').attr('href', '#');

                    var promise = $http.post('/cloud/files/set', {route: $scope.currRoute, filename: file.name});

                    promise.success(function (data) {
                        var dElem = document.getElementById('downloadButton1');
                        dElem.setAttribute('href', '/cloud/files/download');
                    });
                }
            }
        } else {
            $scope.objectClickedFlag = false;
        }
    };

    $scope.deleteFile = function () {
        alertify.confirm(
            "Are you sure you want to delete the file \'" + $scope.fileSelected.name + "\'?",
            function (e) {
                if (e) {
                    var promise = $http.post('/cloud/files/delete', {
                        fileDir: $scope.currRoute,
                        filename: $scope.fileSelected.name
                    });

                    promise.success(function (data) {
                        alertify.success(data);
                        loadFiles($scope.currRoute);
                    }).error(function (data) {
                        alertify.error(data);
                    });
                } else {
                    alertify.log("Process canceled");
                }
            }
        );
    };

    $scope.deleteDirectory = function () {
        alertify.confirm(
            "Are you sure you want to delete the folder \'" + $scope.fileSelected.name + "\'?\n" +
            "The folder and all it's content will be erased!",
            function (e) {
                if (e) {
                    var promise = $http.post('/cloud/dirs/delete', {
                        route: $scope.currRoute,
                        dirname: $scope.fileSelected.name
                    });

                    promise.success(function (data) {
                        alertify.success(data);
                        loadFiles($scope.currRoute);
                    }).error(function (data) {
                        alertify.error(data);
                    });
                } else {
                    alertify.log("Process canceled");
                }
            }
        );
    };

    $scope.sort = function (expression) {
        // If same sort pressed twice
        if (expression == $scope.sortedBy) {
            $scope.reverseSort = !$scope.reverseSort;
        } else {
            $scope.sortedBy = expression;
            $scope.reverseSort = false;
        }

        $scope.files = $filter('orderBy')($scope.files, expression, $scope.reverseSort);
    };

    function loadFiles(path) {
        var filesPromise = $http.post('/cloud/dirs/files', {route: path});

        filesPromise.success(function (data) {
            $scope.files = data.files;
            $scope.sortedBy = "name";
            $scope.reverseSort = false;
        });
    }

    // This function is used to reset saved values that are canceled after clicking something else
    function somethingClicked() {
        $scope.fileSelectedIndex = -1;
        $scope.fileSelected = null;
    }

}]);