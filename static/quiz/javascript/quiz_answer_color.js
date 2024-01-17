function answer_color(good_answer) {
    event.preventDefault();

    // Récupère les cases.
    let box1 = document.getElementById("check1");
    let box2 = document.getElementById("check2");
    let box3 = document.getElementById("check3");
    let text1 = document.getElementById("answer1");
    let text2 = document.getElementById("answer2");
    let text3 = document.getElementById("answer3");

    // Colore les cases.
    if (box1.checked || box2.checked || box3.checked) {

        if (box1.checked) text1.style.color = 'red';
        if (box2.checked) text2.style.color = 'red';
        if (box3.checked) text3.style.color = 'red';
        
        if (good_answer == 0) text1.style.color = 'green';
        if (good_answer == 1) text2.style.color = 'green';
        if (good_answer == 2) text3.style.color = 'green';

    }

    // Passe à la question suivante.
    setTimeout(function () {document.getElementById('question_form').submit()}, 2000);

}