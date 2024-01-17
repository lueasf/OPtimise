// Récupère les cases à cocher.
let box1 = document.getElementById("check1");
let box2 = document.getElementById("check2");
let box3 = document.getElementById("check3");

// Si la case 1 est updatée, met à false les autres.
box1.addEventListener("change", function() {
    box2.checked = false;
    box3.checked = false;
});

// Si la case 1 est updatée, met à false les autres.
box2.addEventListener("change", function() {
    box1.checked = false;
    box3.checked = false;
});

// Si la case 1 est updatée, met à false les autres.
box3.addEventListener("change", function() {
    box1.checked = false;
    box2.checked = false;
});
