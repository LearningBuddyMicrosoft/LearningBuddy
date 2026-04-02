// ================= NAVIGATION =================
function showPage(pageId) {
    document.querySelectorAll(".page").forEach(p =>
        p.classList.remove("active")
    );

    document.getElementById(pageId).classList.add("active");
}


// ================= FILE UPLOAD =================
function uploadFile() {
    let file = document.getElementById("fileInput").files[0];

    if (file) {
        alert("File uploaded: " + file.name);
    } else {
        alert("Please select a file first");
    }
}


// ================= QUIZ START =================
function startQuiz() {
    showPage("quiz");
}


// ================= YOUR QUIZ LOGIC =================
let selectedAnswer = null;

function selectOption(button) {
    let options = document.querySelectorAll(".option-btn");

    // remove previous selection
    options.forEach(btn => btn.classList.remove("selected"));

    // highlight selected
    button.classList.add("selected");

    // store answer
    selectedAnswer = button.innerText;

    // display selected answer
    document.getElementById("selectedText").innerText =
        "You selected: " + selectedAnswer;
}


// ================= NEXT QUESTION =================
function nextQuestion() {
    if (!selectedAnswer) {
        alert("Please select an answer first!");
        return;
    }

    alert("Next question coming (you will connect this later)");

    // reset selection for next question
    selectedAnswer = null;

    document.querySelectorAll(".option-btn").forEach(btn =>
        btn.classList.remove("selected")
    );

    document.getElementById("selectedText").innerText = "";
}


// ================= SUBMIT QUIZ =================
function submitQuiz() {
    if (!selectedAnswer) {
        alert("Please select an answer first!");
        return;
    }

    alert("Quiz submitted! You selected: " + selectedAnswer);

    showPage("history");
}