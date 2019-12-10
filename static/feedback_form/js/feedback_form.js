window.onload = () => {
    console.log("loaded");
    var $form_container = $('.feedback_form');
    var $my_form = $("#feedback_form");
    var values = [];

    $.ajax({
        type: "GET",
        url: "/feedback/",
        data: {
            user_id: $("#user_id").val(),
            csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
            action: "get"
        },
        success: (json) => {
            console.log("success");
            console.log(json);

            // loading html with data
            json.question.forEach((question) => {
                var question_container = document.createElement('div');
                var question_html = document.createElement('textarea');
                var question_label = document.createElement('label');
                var name = 'question_id_' + question.id;

                question_container.setAttribute('class', 'form_input');
                question_label.innerHTML = question.title;
                question_html.setAttribute('name', name);
                question_html.setAttribute('id', question.id);
                question_html.setAttribute('maxlength', "300");

                question_container.appendChild(question_label);
                question_container.appendChild(question_html);

                // appending created html to form
                document.getElementById("feedback_form").appendChild(question_container);
            });

            // creating submit button
            var btn = document.createElement('button');
            btn.setAttribute('type', 'submit');
            btn.innerHTML = "Submit";

            // appending created html to form
            document.getElementById("feedback_title").innerHTML = json[Object.keys(json)[Object.keys(json).length - 1]][0];
            document.getElementById("feedback_note").innerHTML = json[Object.keys(json)[Object.keys(json).length - 1]][1];
            document.getElementById("feedback_form").appendChild(btn);

            $form_container.addClass("js_create");

            var textareas = document.querySelectorAll("#feedback_form textarea");

            textareas.forEach((text) => {
                text.addEventListener("change", (e) => {
                    var data = {
                        question_id: e.target.getAttribute("id"),
                        response: e.target.value
                    };
                    values.push(data);
                });
            });

            document.querySelector(".feedback_form").style.display = "block";

            // adding the textarea height of the last element of the feedback form
            var last_textarea_div = document.querySelectorAll("#feedback_form .form_input");
            var last_textarea = last_textarea_div[Object.keys(last_textarea_div)[Object.keys(last_textarea_div).length - 1]];
            last_textarea.querySelector('textarea').style.height = "150px";
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
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                action: "post"
            },
            success: (json) => {
                console.log("success");
                console.log(json);
                values = [];
                document.getElementById("feedback_form").reset();
            },
            error: (xhr, errmsg, err) => {
                console.log("error");
                console.log(xhr.status + ": " + xhr.responseText);
                values = [];
                document.getElementById("feedback_form").reset();
            }
        });
    });

    var close_form = document.getElementById("close");
    var open_form = document.getElementById("form_close");
    console.log(close);
    close_form.addEventListener('click', e => {
        $form_container.fadeOut();
        console.log("close");
        open_form.classList.add('show');
        open_form.classList.remove('hide');
    });

    open_form.addEventListener('click', e => {
        $form_container.fadeIn();
        console.log("open");
        open_form.classList.add('hide');
        open_form.classList.remove('show');
    });
}