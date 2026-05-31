(function () {
    "use strict";

    const dropzone = document.getElementById("dropzone");
    const input = document.getElementById("file-input");
    const filename = document.getElementById("filename");
    const prompt = document.getElementById("prompt");
    const submit = document.getElementById("submit");

    function reflectSelection() {
        if (!input.files.length) return;
        filename.textContent = input.files[0].name;
        prompt.hidden = true;
        submit.disabled = false;
    }

    input.addEventListener("change", reflectSelection);

    ["dragover", "dragenter"].forEach((type) =>
        dropzone.addEventListener(type, (event) => {
            event.preventDefault();
            dropzone.classList.add("is-active");
        })
    );

    ["dragleave", "drop"].forEach((type) =>
        dropzone.addEventListener(type, (event) => {
            event.preventDefault();
            dropzone.classList.remove("is-active");
        })
    );

    dropzone.addEventListener("drop", (event) => {
        if (!event.dataTransfer.files.length) return;
        input.files = event.dataTransfer.files;
        reflectSelection();
    });
})();
