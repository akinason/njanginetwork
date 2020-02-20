var form_main_container = document.getElementById('feedback_container');
var $form_container = $('.feedback_form');
var $my_form = $("#feedback_form");
var values = [];
var checkbox_data = {
    question_id: null,
    response: [],
    multiple: true
};

$.ajax({
    type: "GET",
    url: "/feedback/",
    data: {
        user_id: $("#user_id").val(),
        csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val()
    },
    success: (data) => {
        console.log("success");
        console.log(data);

        if (data.status === false) {
            console.log("User have not yet submitted");

            // loading html with data
            data.question.forEach((question) => {
                var question_container = document.createElement('div');
                var question_label = document.createElement('label');

                question_container.setAttribute('class', 'form_input');
                question_label.innerHTML = question.title;
                question_container.appendChild(question_label);

                switch (question.data_type) {
                    case 'TEXT':
                        var question_html = document.createElement('input');
                        question_html.setAttribute('type', 'text');
                        question_html.setAttribute('maxlength', "300");
                        question_html.setAttribute('class', "input_text");
                        break;
                    case 'TEXTAREA':
                        var question_html = document.createElement('textarea');
                        question_html.setAttribute('maxlength', "300");
                        question_html.setAttribute('class', "input_textarea");
                        break;
                    case 'OPTION':
                        if (question.multiple === false) {
                            var question_html = document.createElement('select');
                            question_html.setAttribute('class', "input_select");
                            question_html.setAttribute('required', 'required');
                            var default_option = document.createElement('option');
                            default_option.innerHTML = "Select an option"
                            question_html.appendChild(default_option);
                            question.option_list.forEach(option => {
                                var option_html = document.createElement('option')
                                option_html.setAttribute('value', option)
                                option_html.innerHTML = option;
                                question_html.appendChild(option_html);
                            });
                        } else if (question.multiple === true) {
                            var multiple_option = "IS_SET";
                            question.option_list.forEach((option, index) => {
                                var question_html = document.createElement('input');
                                question_html.setAttribute('type', 'checkbox');
                                var option_label = document.createElement('label');
                                option_label.innerHTML = option;

                                question_html.setAttribute('name', `question_id_${question.id}`);
                                question_html.setAttribute('value', option);
                                question_html.setAttribute('class', "input_checkbox");
                                question_html.setAttribute('id', `${question.id}__${index}`);

                                question_container.appendChild(question_html);
                                question_container.appendChild(option_label);
                            })
                        }

                }

                if (typeof multiple_option == 'undefined') {
                    question_html.setAttribute('name', `question_id_${question.id}`);
                    question_html.setAttribute('id', question.id);
                    question_html.setAttribute('required', 'required');

                    question_container.appendChild(question_html);
                }

                // appending created html to form
                document.getElementById("feedback_form").appendChild(question_container);
            });

            // creating submit button
            var btn = document.createElement('button');
            btn.setAttribute('type', 'submit');
            btn.innerHTML = "Submit";
            document.getElementById("feedback_form").appendChild(btn);

            // adding event listeners to all element
            var input_text = document.querySelectorAll("#feedback_form input[type='text']");
            var input_checkbox = document.querySelectorAll("#feedback_form input[type='checkbox']");
            var input_select = document.querySelectorAll("#feedback_form select");
            var input_textareas = document.querySelectorAll("#feedback_form textarea");
            var data = {}

            input_text.forEach(input => {
                input.addEventListener('change', e => {
                    data = {
                        question_id: e.target.getAttribute("id"),
                        response: e.target.value,
                        multiple: false
                    };
                    values.push(data);
                })
            });

            document.querySelector('#feedback_form').addEventListener('click', e => {
                if (e.target.type == 'checkbox') {
                    if (e.target.hasAttribute('checked')) {
                        e.target.removeAttribute('checked');

                        values.forEach(value => {
                            if (value.question_id == e.target.getAttribute('id').split("__")[0]) {
                                value.response = value.response.filter(val => {
                                    return val !== e.target.value
                                })
                            }
                        })

                    } else {
                        e.target.setAttribute('checked', 'checked')
                        checkbox_data.question_id = e.target.getAttribute("id").split("__")[0];

                        checkbox_data.response.push(e.target.value);

                        let exists = false
                        values.forEach(value => {
                            if (value.question_id == e.target.getAttribute('id').split("__")[0]) {
                                if (!value.response.includes(e.target.value)) {
                                    value.response.push(e.target.value);
                                }
                                exists = true;
                            }
                        })

                        if (!exists) {
                            values.push(checkbox_data);
                        }
                    }
                }
            })

            input_select.forEach(select => {
                select.addEventListener('change', e => {
                    data = {
                        question_id: e.target.getAttribute("id"),
                        response: e.target.value,
                        multiple: false
                    };
                    values.push(data);
                })
            })


            input_textareas.forEach(text => {
                text.addEventListener("change", (e) => {
                    data = {
                        question_id: e.target.getAttribute("id"),
                        response: e.target.value,
                        multiple: false
                    };
                    values.push(data);
                });
            });

            document.querySelector(".feedback_form").style.display = "block";

            // adding the textarea height of the last element of the feedback form
            var last_textarea_div = document.querySelectorAll("#feedback_form .form_input");
            var last_textarea = last_textarea_div[Object.keys(last_textarea_div)[Object.keys(last_textarea_div).length - 1]];
            last_textarea.querySelector('textarea').style.height = "150px";

        } else {
            console.log("User have submitted");
            form_main_container.style.display = 'none';
        }

    },
    error: (xhr, errmsg, err) => {
        console.log("error");
        console.log(xhr.status + ": " + xhr.responseText);
    }
});

$my_form.on("submit", e => {
    e.preventDefault();

    $.ajax({
        type: "POST",
        url: "/feedback/",
        data: {
            user_id: $("#user_id").val(),
            response: JSON.stringify(values),
            csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val()
        },
        success: (json) => {
            console.log("success");
            console.log(json);
            values = [];
        },
        error: (xhr, errmsg, err) => {
            console.log("error");
            console.log(xhr.status + ": " + xhr.responseText);
            values = [];
        }
    });
    e.target.reset();
    e.target.querySelectorAll("#feedback_form input[type='checkbox']").forEach(check => {
        if (check.hasAttribute('checked')) {
            check.removeAttribute('checked');
        }
    });
    form_main_container.style.display = 'none';

    // invoke sweet alert
    formApproved();
});

// controlling the feedback form gift open and close on viewpoint 450px
var close_form = document.getElementById("close");
var open_form = document.getElementById("form_close");
close_form.addEventListener('click', e => {
    console.log("close");
    $form_container.fadeOut();
    close_form.classList.remove('show');
    close_form.classList.add('hide');

    form_main_container.style.height = 'unset';
    form_main_container.style.width = 'unset';

    if (window.innerWidth < 451) {
        close_form.classList.add('hide');
        close_form.classList.remove('show');
        open_form.classList.add('show');
        open_form.classList.remove('hide');
    }
});

open_form.addEventListener('click', e => {
    console.log("open");
    $form_container.fadeIn();
    close_form.classList.remove('hide');
    close_form.classList.add('show');

    if (window.innerWidth < 451) {
        close_form.classList.remove('hide');
        close_form.classList.add('show');
        open_form.classList.add('hide');
        open_form.classList.remove('show');
    }
});

window.addEventListener('resize', e => {
    if (e.srcElement.innerWidth < 451) {
        $form_container.fadeIn();
    } else {
        form_main_container.style.height = 'unset';
        form_main_container.style.width = 'unset';

        close_form.classList.remove('hide');
        open_form.classList.remove('hide');
    }
});


// sweet alert js
const formApproved = () => {
    swal({
        text: "Thanks for your collabouration",
        icon: "success",
        button: false,
        timer: 3000
    })
}