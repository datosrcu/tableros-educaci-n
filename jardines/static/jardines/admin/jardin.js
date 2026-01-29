document.addEventListener("DOMContentLoaded", function () {
    const programaSelect = document.getElementById("id_programa");
    const subprogramaSelect = document.getElementById("id_subprograma");

    if (!programaSelect || !subprogramaSelect) return;

    function resetSubprograma() {
        subprogramaSelect.innerHTML = "";
        subprogramaSelect.disabled = true;

        const option = document.createElement("option");
        option.text = "---------";
        option.value = "";
        subprogramaSelect.add(option);
    }

    function cargarSubprogramas(programaId) {
        fetch(`/jardines/ajax/subprogramas/?programa_id=${programaId}`)
            .then(response => response.json())
            .then(data => {
                resetSubprograma();
                data.forEach(sp => {
                    const option = document.createElement("option");
                    option.value = sp.id;
                    option.text = sp.nombre;
                    subprogramaSelect.add(option);
                });
                subprogramaSelect.disabled = false;
            });
    }

    programaSelect.addEventListener("change", function () {
        if (this.value) {
            cargarSubprogramas(this.value);
        } else {
            resetSubprograma();
        }
    });

    // estado inicial
    if (!programaSelect.value) {
        resetSubprograma();
    }
});

