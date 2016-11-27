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
    .run(['$state', function($state){
        $state.go('login')
    }])
    .controller('LoginController', function($scope, $auth, $state) {
        $scope.login = function() {
            console.log($scope.user)
            $auth.login($scope.user)
                .then(function() {
                    console.log('You have successfully signed in!');
                    $state.go('chat')
                })
                .catch(function(error) {
                    console.warn(error.data.message, error.status);
                });
        };
    })
    .controller('ChatController', function() {
        var self = this;
        self.messages = [
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'},
            {user:'User', text:'Hi'}
        ];

        self.addMessage = function() {
            self.messages.push({text:self.newMessage, user: 'New User'});
            self.newMessage = '';
        };
    });

// TODO register
//  TODO login
//  TODO logout