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
            $('#calories-button').show()
            $('#logout-button').show()
        } else {
            $('#login-button').show()
            $('#signup-button').show()
            $('#calories-button').hide()
            $('#logout-button').hide()
        }
    }

    // All the things that need clearning when not logged in.
    var clearLogin = function() {
        clearmessage();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        authButtons();
        $("#caloriesContainer").hide();
    };

    var getSelf = function(callback) {
        clearmessage();
        $.ajax({
            url: '/api/v1/users/self',
            type: 'GET',
            success: function(data, textStatus, xhr) {
                if (data.meta.code === 200) {
                    console.log(data.response);
                    var user = data.response.user;
                    localStorage.setItem('user', JSON.stringify(user));
                    $("#calories_userid").val(user.id);
                    console.log(user.target_daily_calories);
                    $("#target_daily_calories").val(user.target_daily_calories);
                    if (callback) {
                        callback();
                    }
                }
            },
            error: function(data){
                console.log('Error!');
                console.log(data);
            }
        });
    };

    var getMyCalories = function() {
        $("#caloriesContainer").show();
        clearmessage();
        var me = JSON.parse(localStorage.getItem('user'));
        console.log(me);
        $.ajax({
            url: me._links.records,
            type: 'GET',
            success: function(data, textStatus, xhr) {
                if (data.meta.code === 200) {
                    console.log(data.response);
                    var tbody = $("#caloryData");
                    tbody.html('');
                    records = data.response.records;
                    var showdata = '';
                    var todaydate = '';
                    var lastdate = '';
                    var todaysum = 0;
                    var above = [];
                    var below = [];
                    for(var i = 0; i < records.length; i++) {
                        console.log(todaydate);
                        if (todaydate !== records[i].record_date) {
                            if (todaydate.length > 0) {
                                if (todaysum > me.target_daily_calories) {
                                    above.push(".records-"+todaydate);
                                } else {
                                    below.push(".records-"+todaydate);
                                }
                            }
                            todaydate = records[i].record_date;
                            todaysum = 0;
                        }
                        showdata += '<tr class="records-'+records[i].record_date+'">';
                        showdata += '<td>'+records[i].record_date+'</td>';
                        showdata += '<td>'+records[i].record_time+'</td>';
                        showdata += '<td>'+records[i].description+'</td>';
                        showdata += '<td>'+records[i].calories+'</td>';
                        showdata += '<td>Edit</td>';
                        showdata += '<tr>';

                        todaysum += records[i].calories;
                        console.log(todaysum);
                    }
                    if (todaysum > me.target_daily_calories) {
                        above.push(".records-"+todaydate);
                    } else {
                        below.push(".records-"+todaydate);
                    }
                    tbody.append(showdata);
                    for (var i = 0; i < above.length; i++) {
                        $(above[i]).addClass('overTarget');
                        $(above[i]).removeClass('withinTarget');
                    }
                    for (var i = 0; i < below.length; i++) {
                        $(below[i]).removeClass('overTarget');
                        $(below[i]).addClass('withinTarget');
                    }

                }
            },
            error: function(data){
                console.log('Error!');
                console.log(data);
            }
        });
    };


    // On startup
    authButtons();
    getSelf();

    //// Functionality ////

    // Change visibility
    $("button#login-button").click(function() {
        console.log('login form');
        $("div#loginContainer").toggle();
    });

    $("button#signup-button").click(function() {
        console.log('signup form');
        $("div#signupContainer").toggle();
    });

    $("button#calories-button").click(function() {
        console.log('calories');
        getMyCalories();
    });

    $("button#logout-button").click(function() {
        clearmessage()
        $.ajax({
            url: '/logout',
            type: 'GET',
            success: function(data, textStatus, xhr) {
                localStorage.removeItem('auth_token')
                clearLogin();
            },
            error: function(data){
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
                    getSelf();
                    authButtons();
                } else {
                    showmessage("Login unsuccessful!");
                }
            },
            error: function(data){
                alert("Something did not work out, please try again!");
            }
        });
    });

    var addCaloriesForm = $("#caloriesForm");
    var caloriesvalidator = addCaloriesForm.validate();
    caloriesvalidator.form();

    $("#caloriesForm").on('submit', function(e) {
        if (!$("#caloriesForm").valid()) {
            return false;
        }
        clearmessage();
        e.preventDefault();
        var record = {
                record_date: $("#calories_record_date").val(),
                record_time: $("#calories_record_time").val(),
                description: $("#calories_description").val(),
                calories: parseInt($("#calories_calories").val()),
                userid: JSON.parse(localStorage.getItem('user')).id
        };
        console.log(JSON.stringify(record));
        $.ajax({
            url: '/api/v1/records',
            type: 'POST',
            cache: false,
            dataType: 'json',
            data: JSON.stringify(record),
            contentType: "application/json;",
            success: function(data, textStatus, xhr) {
                if (data.meta.code === 200) {
                    $("#caloriesForm")[0].reset();
                    getMyCalories();

                } else {
                    showmessage("Couldn't add calories record!");
                }
            },
            error: function(data){
                alert("Something did not work out, please try again!");
            }
        });
    });


    var dailyCaloriesForm = $("#caloriesTarget");
    var dailyCaloriesValidator = dailyCaloriesForm.validate();
    dailyCaloriesValidator.form();

    dailyCaloriesForm.on('submit', function(e) {
        if (!dailyCaloriesForm.valid()) {
            return false;
        }
        clearmessage();
        e.preventDefault();
        var target = {
                target_daily_calories: parseInt($("#target_daily_calories").val()),
        };
        var userid = JSON.parse(localStorage.getItem('user')).id;
        $.ajax({
            url: '/api/v1/users/'+userid+'/targets',
            type: 'PUT',
            cache: false,
            dataType: 'json',
            data: JSON.stringify(target),
            contentType: "application/json;",
            success: function(data, textStatus, xhr) {
                if (data.meta.code === 200) {
                    getSelf(getMyCalories);
                } else {
                    showmessage("Couldn't add calories target!");
                }
            },
            error: function(data){
                alert("Something did not work out, please try again!");
            }
        });
    });


});
