setTimeout(function () {
    let vozanalize = document.getElementById("btn-analizar-voz");
    let wavanalize = document.getElementById("btn-analizar-wav");

    vozanalize.addEventListener("click", () => analizarvoz());
    wavanalize.addEventListener("click", () => analizarwav());
}, 1000);

function analizarvoz() {
    setTimeout(function () {
        let startButton = document.getElementById("start-button");
        let stopButton = document.getElementById("stop-button");
        let analizeButton = document.getElementById("analizar-boton");

        let mediaStream = null;

        startButton.addEventListener("click", function () {
            navigator.mediaDevices
                .getUserMedia({ audio: true })
                .then(function (stream) {
                    mediaStream = stream;
                    fetch("/start-recording", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ start: true }),
                    })
                        .then((response) => response.json())
                        .then((data) => console.log("Grabación iniciada", data))
                        .catch((error) =>
                            console.error("Error al iniciar la grabación:", error)
                        );
                })
                .catch(function (err) {
                    console.log("Permiso denegado: " + err.name);
                });
        });

        stopButton.addEventListener("click", function () {
            // Detener todos los tracks del micrófono
            if (mediaStream) {
                let tracks = mediaStream.getTracks();
                tracks.forEach((track) => track.stop());
                mediaStream = null;
            }

            fetch("/stop-recording", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ stop: true }),
            })
                .then((response) => response.json())
                .then((data) => console.log("Grabación detenida", data))
                .catch((error) =>
                    console.error("Error al detener la grabación:", error)
                );
        });

        analizeButton.addEventListener("click", () => analizarwav());

    }, 1000);
}

function analizarwav() {
    setTimeout(function () {
        let audioPlayer = document.getElementById("audio-player");

        if (audioPlayer) {
            audioPlayer.addEventListener("timeupdate", function () {
                let currentTime = audioPlayer.currentTime;
                // Selecciona las gráficas y actualiza la posición de la línea
                let figures2d = document.querySelectorAll(".cursor2d");
                figures2d.forEach((fig) => {
                    // Encuentra el contenedor interno de Plotly
                    let plotlyContainer = fig.querySelector(".js-plotly-plot");

                    if (plotlyContainer) {
                        try {
                            Plotly.relayout(plotlyContainer, {
                                shapes: [
                                    {
                                        type: "line",
                                        x0: currentTime,
                                        x1: currentTime,
                                        y0: 0,
                                        y1: 1,
                                        xref: "x",
                                        yref: "paper",
                                        line: {
                                            color: "red",
                                            width: 2,
                                        },
                                    },
                                ],
                            });
                        } catch (err) {
                            console.error("Error updating plot:", err);
                        }
                    } else {
                        console.error(
                            `Element with ID ${fig.id} is not initialized as a Plotly graph.`
                        );
                    }
                });
            });
        }
    }, 1000);
}
