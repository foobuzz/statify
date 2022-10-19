function initSongChart(spotifyId) {
    fetch(`/api/listenings/${spotifyId}`).then(function(response) {
        response.text().then(function(text) {
            listenings = JSON.parse(text);
            timeData = convertListeningsToTimeSeries(listenings);
            const config = {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        data: timeData,
                        label: "# Listenings",
                        borderColor: "#3e95cd",
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        x: {
                            type: 'time'
                        }
                    },
                    maintainAspectRatio: false,
                }
            };
            const myChart = new Chart(
                document.getElementById('songChart'),
                config,
            );
        });
    });
}


function convertListeningsToTimeSeries(listenings) {
    let timeData = [];
    listenings.forEach(function(listening, index) {
        timeData.push({
            x: new Date(listening.played_at * 1000),
            y: index + 1,
        });
    });
    return timeData;
}


document.addEventListener('DOMContentLoaded', function() {
    initSongChart(JS_INIT_DATA.spotifyId);
});
