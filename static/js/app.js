angular.module('chatApp', ['ui.router', 'satellizer', 'ngResource'])
    .config(function($stateProvider, $authProvider, $qProvider) {
        var loginState = {
            name: 'login',
            url: '/login',
            templateUrl: '/static/html/login.html',
            controller: 'LoginController'
        }

        var chatState = {
            name: 'chat',
            url: '/chat',
            templateUrl: '/static/html/chat.html',
            controller: 'ChatController'
        }

        $stateProvider.state(loginState);
        $stateProvider.state(chatState);

        $authProvider.baseUrl = '/';
        $authProvider.loginUrl = '/login';
        $authProvider.signupUrl = '/registration';
        $authProvider.unlinkUrl = '/auth/unlink/';
        $authProvider.tokenName = 'token';
        $authProvider.tokenPrefix = 'satellizer';
        $authProvider.tokenHeader = 'Authorization';
        $authProvider.tokenType = 'JWT';
        $authProvider.storageType = 'localStorage';

        $qProvider.errorOnUnhandledRejections(false);
    })
    .run(['$auth', '$state', function($auth, $state){
        if ($auth.isAuthenticated()) {
            $state.go('chat');
        } else {
            $state.go('login')
        }
    }])
    .controller('LoginController', function($scope, $auth, $state) {
        if ($auth.isAuthenticated()) {
            $state.go('chat');
        }
        $scope.login = function() {
            console.log($scope.user)
            $auth.login($scope.user)
                .then(function() {
                    console.log('You have successfully signed in!');
                    console.log($auth.isAuthenticated())
                    $state.go('chat')
                })
                .catch(function(error) {
                    console.warn(error.data.message, error.status);
                });
        };
    })
    .factory('Message', ['$resource', function($resource) {
        return $resource('/chat');
    }])
    .controller('ChatController', function($auth, $state, Message) {
        var self = this;
        self.messages = Message.query();
        self.message = new Message()

        self.addMessage = function() {
            if (!self.message) return;
            self.message.$save(function(message) {
                self.messages.push(message);
            });
            self.message = new Message();
        };
        self.logout = function() {
            $auth.logout();
            $state.go('login');
        }
    });

//  TODO register