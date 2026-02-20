(function($) {
    $(document).ready(function() {
        const programaField = $("#id_programa");
        const subprogramaField = $("#id_subprograma");

        function cargarSubprogramas(programaId) {
            subprogramaField.empty();
            subprogramaField.append(
                $('<option></option>').val('').text('---------')
            );

            if (!programaId) return;

            $.ajax({
                url: "/jardines/ajax/subprogramas/",
                data: {
                    programa_id: programaId
                },
                success: function(data) {
                    data.forEach(function(item) {
                        subprogramaField.append(
                            $('<option></option>')
                                .val(item.id)
                                .text(item.nombre)
                        );
                    });
                }
            });
        }

        programaField.change(function() {
            cargarSubprogramas($(this).val());
        });

        // 🔄 Si estamos editando un objeto existente
        if (programaField.val()) {
            cargarSubprogramas(programaField.val());
        }
    });
})(django.jQuery);
