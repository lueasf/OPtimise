function update_progress_bar(size) {

    // Met à jour la taille de la bare de progression.
    var progression = document.getElementById("progression"); 
    let width = 100*size + "%";
    progression.style.width = width; 

}