var messageContainer = document.getElementById("output"),
    sparkline_options = {
        curveType: 'function',
        interpolateNulls: true,
        legend: {
            position: 'none'
        },
        axisTitlesPosition: 'none',
        titlePosition: 'none',
        hAxis: {
            'baselineColor': 'none',
            'textPosition': 'none',
            'gridlines': {
                'count': 0
            }
        },
        vAxis: {
            'baselineColor': 'none',
            'textPosition': 'none',
            'gridlines': {
                'count': 0
            }
        },
        tooltip: {
            trigger: 'none'
        },
        chartArea: {
            'width': '100%',
            'height': '100%'
        }
    };

openWebSocket();
google.setOnLoadCallback(drawCharts);

// Make sure that graphs resize nicely with the window.
$(window).resize(function () {
    drawCharts();
});

function drawCharts() {
    Object.keys(sparkline_data).forEach(function (key) {
        var chart = new google.visualization.LineChart(document.getElementById(key));
        chart.draw(sparkline_data[key], sparkline_options);
    });
}

function openWebSocket() {

    if ("WebSocket" in window) {
        var url = "ws://127.0.0.1:8080/ws/",
            ws = new WebSocket(url);

        messageContainer.innerHTML = "WebSocket are supported by your Browser!";

        ws.onopen = function () {
            messageContainer.innerHTML = 'connected';
        };

        ws.onmessage = function (evt) {
            var received_msg = evt.data,
                data = $.parseJSON(received_msg),
                d = new Date(data.datetime * 1000),
                curr_hour = d.getHours(),
                curr_min = d.getMinutes(),
                spark_ref = "spark_" + data.service + "_" + data.user_account;

            messageContainer.innerHTML = messageContainer.innerHTML + '<br />' + received_msg;

            // Update follower count below sparkline
            $('#' + data.service + "_" + data.user_account + " .count").text(data.followers);
            $('.' + data.service + " #last_updated").text(curr_hour + ":" + curr_min);

            if (sparkline_data[spark_ref].getNumberOfRows <= 40) {
                sparkline_data[spark_ref].removeRow(39);
            }
            sparkline_data[spark_ref].insertRows(0, [[new Date(data.datetime * 1000), data.followers]]);

            drawCharts();
        };

        ws.onclose = function () {
            messageContainer.innerHTML = "Connection is closed...";
        };

    } else {
        messageContainer.innerHTML = "WebSocket are NOT supported by your Browser. :-(";
    }

}