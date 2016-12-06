angular.module('chatApp', ['ui.router', 'satellizer', 'ngResource'])
    .config(function($stateProvider, $authProvider, $qProvider) {
        var loginState = {
            name: 'login',
            url: '/login',
            templateUrl: '/static/html/login.html',
            controller: 'LoginController'
        }

        var signUpState = {
            name: 'signUp',
            url: '/sign_up',
            templateUrl: '/static/html/registration.html',
            controller: 'SignUpController'
        }

        var chatState = {
            name: 'chat',
            url: '/chat',
            templateUrl: '/static/html/chat.html',
            controller: 'ChatController'
        }

        $stateProvider.state(loginState);
        $stateProvider.state(signUpState);
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
    .factory('Message', ['$resource', function($resource) {
        return $resource('/chat');
    }])
    .factory('User', ['$resource', function($resource) {
        return $resource('/registration');
    }])
    .controller('LoginController', function($auth, $state) {
        var self = this;
        if ($auth.isAuthenticated()) {
            $state.go('chat');
        }
        self.login = function() {
            console.log(self.user)
            $auth.login(self.user)
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
    .controller('SignUpController', function($auth, $state, User) {
        var self = this;
        if ($auth.isAuthenticated()) {
            $state.go('chat');
        }
        self.user = new User();
        self.register = function() {
            if (self.user.password1 === self.user.password2) {
                self.user.password = self.user.password1;
                self.user.$save(function(user) {
                    $state.go('login');
                }, function() {
                    alert('FAIL!!!');
                });
            }
        };
    })
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