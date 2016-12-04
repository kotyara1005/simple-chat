console.log('app.js');

angular.module('chatApp', ['ui.router', 'satellizer'])
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
    .controller('ChatController', function($auth, $state) {
        var self = this;
        self.messages = [];

        self.addMessage = function() {
            self.messages.push({text: self.message, user: 'New User'});
            self.message = '';
        };
        self.logout = function() {
            $auth.logout();
            $state.go('login')
        }
    });

//  TODO register
//  TODO logout