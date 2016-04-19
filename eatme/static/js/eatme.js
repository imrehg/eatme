$(document).ready(function() {

    var showmessage = function(message) {
        $("#messageField").text(message);
    }
    var clearmessage = function() {
        showmessage('');
    }

    var authButtons = function() {
        clearmessage();
        if (localStorage.getItem('auth_token')) {
            $('#login-button').hide()
            $('#signup-button').hide()
            $('#logout-button').show()
        } else {
            $('#login-button').show()
            $('#signup-button').show()
            $('#logout-button').hide()
        }
    }
    authButtons();

    // Change visibility
    $("button#login-button").click(function() {
        console.log('login form');
        $("div#loginContainer").toggle();
    });

    $("button#signup-button").click(function() {
        console.log('signup form');
        $("div#signupContainer").toggle();
    });

    $("button#logout-button").click(function() {
        clearmessage()
        $.ajax({
            url: '/logout',
            type: 'GET',
            success: function(data, textStatus, xhr) {
                localStorage.removeItem('auth_token')
                authButtons();
            },
            error: function(data){
                console.log(data)
                alert("Something did not work out, please try again!");
            }
        });
    });

    // Signup Form
    var signupform = $("#signupForm");
    var signupvalidator = signupform.validate({
        rules: {
            password2: {
                equalTo: "#signupPW1"
            }
        }
    });
    signupvalidator.form();

    $('form#signupForm').on('submit', function(e) {
        clearmessage()
        var person = {
                email: $("#signupEmail").val(),
                password: $("#signupPW1").val()
        }
        console.log(person);
        $.ajax({
            url: '/api/v1/users',
            type: 'POST',
            cache: false,
            dataType: 'json',
            data: JSON.stringify(person),
            contentType: "application/json;",
            success: function (data) {
                $('form#signupForm')[0].reset();
                $("div#signupContainer").hide();
                $("div#loginContainer").show();
            },
            error: function(data){
                showmessage("Signup unsuccessfu!");
            }
        });
        e.preventDefault();
    });

    // Login Form
    var loginform = $("#loginForm");
    var loginvalidator = loginform.validate();
    loginvalidator.form();

    $('form#loginForm').on('submit', function(e) {
        clearmessage()
        var person = {
                email: $("#loginEmail").val(),
                password: $("#loginPW").val()
        }
        console.log(person)
        e.preventDefault();
        $.ajax({
            url: '/login',
            type: 'POST',
            cache: false,
            cache: false,
            dataType: 'json',
            data: JSON.stringify(person),
            contentType: "application/json;",
            success: function(data, textStatus, xhr) {
                if (data.meta.code === 200) {
                    localStorage.setItem('auth_token', data.response.user.authentication_token)
                    $('form#loginForm')[0].reset();
                    $("div#signupContainer").hide();
                    $("div#loginContainer").hide();
                    authButtons();
                } else {
                    showmessage("Login unsuccessfu!");
                }
            },
            error: function(data){
                console.log(data)
                alert("Something did not work out, please try again!");
            }
        });
    });


});


//$.ajax({
//    url: 'http://api',
//    type: 'GET',
//    dataType: 'json',
//    beforeSend: function (xhr) {
//        xhr.setRequestHeader(
//                'Authorization',
//                'Basic ' + btoa('username:password'));
//    }
//}).complete(function () {
//
//}).fail(function () {
//
//});