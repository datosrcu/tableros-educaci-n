document.addEventListener("DOMContentLoaded", function () {
    const jardin = document.getElementById("id_jardin");
    const turno = document.getElementById("id_turno");
    const nombre = document.getElementById("id_nombre");

    function validar() {
        if (!jardin.value) {
            jardin.style.border = "2px solid red";
        } else {
            jardin.style.border = "";
        }

        if (!turno.value) {
            turno.style.border = "2px solid red";
        } else {
            turno.style.border = "";
        }

        if (!nombre.value.trim()) {
            nombre.style.border = "2px solid red";
        } else {
            nombre.style.border = "";
        }
    }

    jardin?.addEventListener("change", validar);
    turno?.addEventListener("change", validar);
    nombre?.addEventListener("input", validar);
});
