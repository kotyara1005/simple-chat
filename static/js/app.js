console.log('app.js');

angular.module('chatApp', ['ui.router'])
    .config(function($stateProvider) {
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
    })
    .run(['$state', function($state){
      $state.go('login')
    }])
    .controller('LoginController', function() {
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

//  TODO routing
//  TODO login
//  TODO logout